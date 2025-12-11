import feedparser
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import time

# --- 1. AYARLAR VE KURULUMLAR ---

# NLTK Hatasını önlemek için gerekli indirmeler (Otomatik kontrol eder)
def setup_nltk():
    resources = ['punkt', 'vader_lexicon', 'stopwords']
    for res in resources:
        try:
            nltk.data.find(f'tokenizers/{res}') if res == 'punkt' else nltk.data.find(f'sentiment/{res}')
        except LookupError:
            print(f"NLTK verisi indiriliyor: {res}...")
            nltk.download(res, quiet=True)

setup_nltk()

# Duygu Analizcisi Başlat
sia = SentimentIntensityAnalyzer()

# --- 2. VARLIK HARİTASI (TRACKED STOCKS) ---
# Haber metnindeki kelimeleri Borsa Kodlarıyla (Ticker) eşleştirir.
TRACKED_STOCKS = {
    # Teknoloji Devleri
    "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL",
    "amazon": "AMZN", "nvidia": "NVDA", "meta": "META", "facebook": "META",
    "tesla": "TSLA",
    # Çip ve Donanım
    "broadcom": "AVGO", "qualcomm": "QCOM", "intel": "INTC", "amd": "AMD",
    "micron": "MU", "texas instruments": "TXN", "analog devices": "ADI",
    # Yazılım ve Servisler
    "adobe": "ADBE", "salesforce": "CRM", "oracle": "ORCL", "ibm": "IBM",
    "paypal": "PYPL", "netflix": "NFLX",
    # Diğer
    "cisco": "CSCO", "at&t": "T", "disney": "DIS"
}

# Takip edilecek Haber Kaynakları (RSS) - US Markets Odaklı
RSS_URLS = [
    "https://finance.yahoo.com/news/rssindex",
    "http://feeds.marketwatch.com/marketwatch/marketpulse",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664" # CNBC Technology
]

# Sonuçların Kaydedileceği Dosya
OUTPUT_FILE = "sazlik_signals.csv"

# --- 3. FONKSİYONLAR ---

def get_market_data(ticker):
    """
    Verilen hisse için Yahoo Finance'den anlık fiyat, değişim ve hacim çeker.
    """
    try:
        stock = yf.Ticker(ticker)
        # Sadece son 1 günün verisi (periyot kısa tutulup hız kazanılır)
        hist = stock.history(period="1d")
        
        if hist.empty:
            return None
        
        current_price = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[-1]
        volume = hist['Volume'].iloc[-1]
        
        # Yüzdelik Değişim Hesabı
        change_pct = ((current_price - open_price) / open_price) * 100
        
        return {
            "price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "volume": volume
        }
    except Exception as e:
        # Hata olursa (örn: piyasa kapalıyken veri yoksa) None dön
        return None

def analyze_sentiment(text):
    """
    Haber metnine duygu analizi yapar.
    Skor: -1 (Çok Negatif) ile +1 (Çok Pozitif) arasındadır.
    """
    score = sia.polarity_scores(text)
    return score['compound']

def determine_signal(sentiment, change_pct):
    """
    Haber Duygusu + Fiyat Değişimi = Sinyal
    """
    # Basit bir mantık: Haber iyi VE Fiyat artıyorsa -> GÜÇLÜ AL
    if sentiment > 0.5 and change_pct > 0:
        return "GÜÇLÜ AL (Momentum)"
    elif sentiment > 0.2 and change_pct > -1:
        return "AL (Haber Pozitif)"
    elif sentiment < -0.5 and change_pct < 0:
        return "GÜÇLÜ SAT (Panik)"
    elif sentiment < -0.2:
        return "SAT (Haber Negatif)"
    else:
        return "NÖTR / İZLE"

# --- 4. ANA ÇALIŞMA DÖNGÜSÜ ---

def run_news_bot():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Haber Avcısı Başlatılıyor...")
    all_signals = []

    for url in RSS_URLS:
        print(f"-> Kaynak taranıyor: {url}")
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            title = entry.title
            summary = entry.summary if 'summary' in entry else title
            published = entry.published if 'published' in entry else str(datetime.now())
            
            # 1. Adım: Başlıkta takip ettiğimiz hisse var mı?
            matched_ticker = None
            for keyword, ticker in TRACKED_STOCKS.items():
                if keyword in title.lower():
                    matched_ticker = ticker
                    break
            
            if matched_ticker:
                print(f"   BULUNDU: {matched_ticker} -> {title[:50]}...")
                
                # 2. Adım: Piyasa Verilerini Çek
                market_data = get_market_data(matched_ticker)
                
                # 3. Adım: Duygu Analizi Yap
                sentiment_score = analyze_sentiment(title + " " + summary)
                
                if market_data:
                    # 4. Adım: Sinyal Üret
                    signal = determine_signal(sentiment_score, market_data['change_pct'])
                    
                    signal_data = {
                        "Tarih": datetime.now().strftime('%Y-%m-%d %H:%M'),
                        "Hisse": matched_ticker,
                        "Haber_Baslik": title,
                        "Duygu_Skoru": sentiment_score,
                        "Fiyat": market_data['price'],
                        "Degisim_Yuzde": market_data['change_pct'],
                        "Hacim": market_data['volume'],
                        "Sinyal": signal,
                        "Link": entry.link
                    }
                    all_signals.append(signal_data)
                    print(f"      ✅ SİNYAL: {signal} | Fiyat: {market_data['price']} ({market_data['change_pct']}%)")
                else:
                    print("      ⚠️ Piyasa verisi alınamadı (Piyasa kapalı olabilir).")

    # --- 5. SONUÇLARI KAYDETME ---
    if all_signals:
        df = pd.DataFrame(all_signals)
        
        # Eğer dosya varsa ekle, yoksa yeni oluştur (mode='a' append)
        if os.path.exists(OUTPUT_FILE):
            df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
        else:
            df.to_csv(OUTPUT_FILE, mode='w', header=True, index=False)
            
        print(f"\nToplam {len(all_signals)} yeni sinyal '{OUTPUT_FILE}' dosyasına kaydedildi.")
    else:
        print("\nİlgili hisseler hakkında yeni bir haber bulunamadı.")

if __name__ == "__main__":
    run_news_bot()
