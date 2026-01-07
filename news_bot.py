import yfinance as yf
import pandas as pd
import feedparser
import google.generativeai as genai
from datetime import datetime
import time
# ESKİSİ GİTTİ: import pandas_ta as ta
# YENİSİ GELDİ:
import ta 
from config import GEMINI_API_KEY, WATCHLIST_TICKERS, RSS_URLS, OUTPUT_FILE

# Gemini Ayarları
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_technical_analysis(ticker):
    """
    yfinance ile veri çeker ve 'ta' kütüphanesi ile RSI ve SMA hesaplar.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if df.empty:
            return None

        # --- YENİ KÜTÜPHANE İLE HESAPLAMA ---
        # RSI Hesaplama (14 günlük)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        # SMA (Hareketli Ortalamalar)
        df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
        # ------------------------------------

        current_price = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]
        
        signal = "NÖTR"
        score = 50
        
        # Basit Teknik Puanlama
        if rsi < 30: 
            score += 20  # Aşırı satım (Al fırsatı olabilir)
        elif rsi > 70: 
            score -= 20  # Aşırı alım (Sat sinyali)
            
        if current_price > sma_50: score += 10
        if current_price > sma_200: score += 10
        if sma_50 > sma_200: score += 10  # Golden Cross sinyali
        
        return {
            "Fiyat": current_price,
            "RSI": rsi,
            "SMA_50": sma_50,
            "SMA_200": sma_200,
            "Teknik_Skor": score
        }
    except Exception as e:
        # print(f"Hata ({ticker}): {e}") 
        return None

def analyze_news_sentiment(text):
    """
    Gemini AI ile haber metnini analiz eder.
    """
    try:
        prompt = f"""
        Aşağıdaki finans haberini analiz et ve bu şirketin hisse senedi için -100 (Çok Kötü) ile +100 (Çok İyi) arasında bir puan ver.
        Sadece puanı yaz, başka hiçbir şey yazma.
        
        Haber: {text}
        """
        response = model.generate_content(prompt)
        puan = int(response.text.strip())
        return puan
    except:
        return 0

def fetch_market_news():
    """
    RSS kaynaklarından genel piyasa haberlerini çeker.
    """
    news_sentiment = 0
    count = 0
    print("🌍 Piyasa Haberleri Taranıyor...")
    
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # Her kaynaktan en son 3 haber
                puan = analyze_news_sentiment(entry.title)
                news_sentiment += puan
                count += 1
        except:
            continue
            
    if count > 0:
        return news_sentiment / count
    return 0

def run_news_bot():
    """
    Ana fonksiyon: Tüm listeyi tarar, teknik ve temel analiz yapar.
    """
    print(f"🚀 Sazlık Analiz Motoru Çalışıyor... ({len(WATCHLIST_TICKERS)} Hisse)")
    
    market_sentiment = fetch_market_news()
    print(f"📊 Genel Piyasa Duygusu: {market_sentiment:.2f}")
    
    results = []
    
    for symbol in WATCHLIST_TICKERS:
        # Teknik Analiz
        tech_data = get_technical_analysis(symbol)
        if not tech_data:
            continue
            
        final_score = tech_data['Teknik_Skor'] + (market_sentiment * 0.3)
        
        # 0-100 Arasına Sabitle
        final_score = max(0, min(100, final_score))
        
        results.append({
            "Hisse": symbol,
            "Fiyat": round(tech_data['Fiyat'], 2),
            "RSI": round(tech_data['RSI'], 2),
            "Guven_Skoru": round(final_score, 1),
            "Sinyal": "AL" if final_score > 75 else "SAT" if final_score < 40 else "TUT"
        })
        print(f"✅ {symbol} Analiz Edildi. Skor: {final_score:.1f}")
        
    # Sonuçları Kaydet
    if results:
        df = pd.DataFrame(results)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"💾 Sonuçlar {OUTPUT_FILE} dosyasına kaydedildi.")
        return len(results)
    else:
        print("❌ Hiçbir sonuç üretilemedi.")
        return 0

if __name__ == "__main__":
    run_news_bot()