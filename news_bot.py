import feedparser
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import time

# config.py dosyasından ayarları çekiyoruz
from config import TRACKED_STOCKS, RSS_URLS, OUTPUT_FILE

# --- 1. AYARLAR VE KURULUMLAR ---

def setup_nltk():
    resources = ['punkt', 'vader_lexicon', 'stopwords']
    for res in resources:
        try:
            nltk.data.find(f'tokenizers/{res}') if res == 'punkt' else nltk.data.find(f'sentiment/{res}')
        except LookupError:
            print(f"NLTK verisi indiriliyor: {res}...")
            nltk.download(res, quiet=True)

setup_nltk()
sia = SentimentIntensityAnalyzer()

# --- 2. FONKSİYONLAR ---

def get_market_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        
        if hist.empty:
            return None
        
        current_price = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[-1]
        volume = hist['Volume'].iloc[-1]
        change_pct = ((current_price - open_price) / open_price) * 100
        
        return {
            "price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "volume": volume
        }
    except Exception as e:
        return None

def analyze_sentiment(text):
    score = sia.polarity_scores(text)
    return score['compound']

def determine_signal(sentiment, change_pct):
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

# --- 3. ANA ÇALIŞMA DÖNGÜSÜ ---

def run_news_bot():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Haber Avcısı Başlatılıyor...")
    all_signals = []

    for url in RSS_URLS:
        print(f"-> Kaynak taranıyor: {url}")
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            title = entry.title
            summary = entry.summary if 'summary' in entry else title
            
            # Başlıkta takip ettiğimiz hisse var mı?
            matched_ticker = None
            for keyword, ticker in TRACKED_STOCKS.items():
                if keyword in title.lower():
                    matched_ticker = ticker
                    break
            
            if matched_ticker:
                print(f"   BULUNDU: {matched_ticker} -> {title[:50]}...")
                market_data = get_market_data(matched_ticker)
                sentiment_score = analyze_sentiment(title + " " + summary)
                
                if market_data:
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
                    print(f"      ✅ SİNYAL: {signal} | Fiyat: {market_data['price']}")
                else:
                    print("      ⚠️ Piyasa verisi alınamadı.")

    # Kayıt İşlemi
    if all_signals:
        df = pd.DataFrame(all_signals)
        if os.path.exists(OUTPUT_FILE):
            df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
        else:
            df.to_csv(OUTPUT_FILE, mode='w', header=True, index=False)
        print(f"\nToplam {len(all_signals)} yeni sinyal kaydedildi.")
    else:
        print("\nİlgili hisseler hakkında yeni bir haber bulunamadı.")

if __name__ == "__main__":
    run_news_bot()
