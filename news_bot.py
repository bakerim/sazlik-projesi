import feedparser
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
import os
import time
import json
import random
from datetime import datetime
from config import TRACKED_STOCKS, RSS_URLS, OUTPUT_FILE, WATCHLIST_TICKERS

# API AYARLARI
API_KEY = os.environ.get("GEMINI_API_KEY") 
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

# --- TURBO GARANTİCİ BABA ANALİZİ (SİGORTALI) ---
def garantici_baba_analiz(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Hız ve momentum hesabı için son 3 ay yeterli
        df = stock.history(period="3mo") 
        if len(df) < 50: return None 
        
        current_price = df['Close'].iloc[-1]

        # --- SİGORTA: 20 GÜNLÜK MOMENTUM KONTROLÜ ---
        # Mantık: Hisse son 1 ayda (20 işlem günü) sürünüyorsa, bize yaramaz.
        # Bugünün fiyatı, 20 gün önceki fiyattan büyük olmak ZORUNDA.
        try:
            price_20_days_ago = df['Close'].iloc[-21]
            if current_price <= price_20_days_ago:
                return None # ELEDİK (Zaman Kaybı)
        except:
            return None # Veri hatası varsa riske girme

        # --- İNDİKATÖRLER ---
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=20, append=True)
        df.ta.atr(length=14, append=True)
        
        rsi = df['RSI_14'].iloc[-1]
        ema20 = df['EMA_20'].iloc[-1]
        atr = df['ATRr_14'].iloc[-1]
        
        if pd.isna(rsi) or pd.isna(atr): return None

        # HIZ HESABI (ATR / Fiyat)
        hiz_yuzdesi = (atr / current_price) * 100
        
        # SÜZGEÇ: Çok hantal hisseleri (Günde %1.5 altı) ele
        if hiz_yuzdesi < 1.5: return None

        # --- PUANLAMA ---
        score = 50
        sebepler = []
        
        # 1. Trend (EMA20)
        if current_price > ema20:
            score += 30
            sebepler.append("Trend Yukarı")
        
        # 2. RSI (Momentum)
        if 50 <= rsi <= 65:
            score += 30
            sebepler.append("RSI Patlamaya Hazır")
        elif rsi < 30:
            score += 20
            sebepler.append("Dip Tepkisi")
        elif rsi > 70:
            score -= 10
            sebepler.append("Aşırı Şişik")

        # 3. Hız Bonusu
        if hiz_yuzdesi > 3.0:
            score += 20
            sebepler.append("Volatilite Yüksek")
        
        # Karar Mekanizması
        karar = "BEKLE"
        if score >= 80: karar = "GÜÇLÜ AL"
        elif score >= 60: karar = "AL"
        
        # Süre Hesabı (%5 Hedef için)
        gun_tahmini = max(1, int(5 / hiz_yuzdesi))
        vade_str = f"1-{gun_tahmini + 1} Gün"

        analiz_metni = " | ".join(sebepler)
        
        return {
            "karar": karar,
            "guven_skoru": score,
            "analiz_ozeti": analiz_metni,
            "fiyat": round(current_price, 2),
            "rsi": round(rsi, 2),
            "hedef_fiyat": round(current_price * 1.05, 2), # %5 Hedef
            "stop_loss": round(current_price * 0.96, 2),   # %4 Stop
            "vade": vade_str,
            "hiz": round(hiz_yuzdesi, 2)
        }
    except:
        return None

# --- ANA MOTOR ---
def run_news_bot():
    print("🧠 Sazlık Motoru: Sigortalı Tarama Başlıyor...")
    
    all_signals = []
    

    target_list = WATCHLIST_TICKERS 
    scan_limit = 350
    scan_list = random.sample(target_list, min(len(target_list), scan_limit))

    for ticker in scan_list:
        try:
            res = garantici_baba_analiz(ticker)
            # Sadece 60 puan üstünü (AL/GÜÇLÜ AL) kaydet
            if res and res['guven_skoru'] >= 60:
                signal = {
                    "Tarih": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "Hisse": ticker,
                    "Fiyat": res['fiyat'],
                    "Karar": res['karar'],
                    "Hedef_Fiyat": res['hedef_fiyat'],
                    "Stop_Loss": res['stop_loss'],
                    "Guven_Skoru": res['guven_skoru'],
                    "Vade": res['vade'],
                    "Analiz_Ozeti": res['analiz_ozeti'],
                    "Haber_Baslik": "Teknik Sinyal",
                    "Link": f"https://finance.yahoo.com/quote/{ticker}",
                    "hiz": res['hiz']
                }
                all_signals.append(signal)
        except: continue

    # CSV KAYIT İŞLEMLERİ
    if all_signals:
        df = pd.DataFrame(all_signals)
        if os.path.exists(OUTPUT_FILE):
             try:
                 old_df = pd.read_csv(OUTPUT_FILE)
                 combined = pd.concat([df, old_df])
                 combined = combined.drop_duplicates(subset=['Hisse'], keep='first')
                 combined.to_csv(OUTPUT_FILE, index=False)
                 return len(all_signals)
             except:
                 df.to_csv(OUTPUT_FILE, index=False)
                 return len(all_signals)
        else:
             df.to_csv(OUTPUT_FILE, index=False)
             return len(all_signals)
    
    # HATA ÖNLEYİCİ: Hiçbir şey bulamazsa 0 döndür
    return 0 

if __name__ == "__main__":
    run_news_bot()
