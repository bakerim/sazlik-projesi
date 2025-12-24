import feedparser
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
import os
import time
import json
from datetime import datetime
from config import TRACKED_STOCKS, RSS_URLS, OUTPUT_FILE, WATCHLIST_TICKERS

# API AYARLARI
API_KEY = os.environ.get("GEMINI_API_KEY") 
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

# --- GADDAR PUANLAMA MOTORU (SİGORTALI) ---
def garantici_baba_analiz(ticker):
    try:
        stock = yf.Ticker(ticker)
        # SMA50 ve trendi sağlıklı ölçmek için 6 aylık veri çekiyoruz
        df = stock.history(period="6mo") 
        if len(df) < 100: return None 
        
        current_price = df['Close'].iloc[-1]
        
        # --- 1. SİGORTA: 20 GÜN KURALI (ELEME) ---
        # Hisse son 1 ayda (20 işlem günü) para kazandırmadıysa, bize de kazandırmaz.
        try:
            price_20_days_ago = df['Close'].iloc[-21]
            if current_price <= price_20_days_ago:
                return None # 20 gün öncesinden kötüyse direkt ÇÖP. Eledik.
        except: return None

        # --- İNDİKATÖRLERİN HESAPLANMASI ---
        df.ta.rsi(length=14, append=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.atr(length=14, append=True)
        
        # Son güncel veriler
        rsi = df['RSI_14'].iloc[-1]
        sma20 = df['SMA_20'].iloc[-1]
        sma50 = df['SMA_50'].iloc[-1]
        atr = df['ATRr_14'].iloc[-1]
        
        # Hacim verileri
        vol_now = df['Volume'].iloc[-1]
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1]

        if pd.isna(rsi) or pd.isna(atr): return None

        # --- GADDAR PUANLAMA SİSTEMİ (MAX 100) ---
        score = 0
        sebepler = []

        # 1. TREND PUANI (Max 30 Puan)
        # Fiyat SMA20 üstündeyse +15, SMA50 üstündeyse +15
        if current_price > sma20: score += 15
        if current_price > sma50: score += 15
        
        if score == 30: sebepler.append("Trend: Mükemmel")
        elif score == 15: sebepler.append("Trend: Zayıf")
        else: sebepler.append("Trend: Çöküş")

        # 2. RSI HASSAS PUANLAMA (Max 25 Puan)
        # Hedefimiz RSI 60. Buradan ne kadar uzaksa o kadar puan kır.
        # RSI 60 ise: 25 Puan. RSI 40 ise: 5 Puan.
        ideal_rsi = 60
        mesafe = abs(ideal_rsi - rsi)
        rsi_puan = max(0, 25 - int(mesafe)) # Her 1 birim sapma 1 puan götürür
        score += rsi_puan
        sebepler.append(f"RSI Puanı: {rsi_puan}/25")

        # 3. HACİM PUANI (Max 20 Puan)
        # Hacim ortalamanın kaç katı? (Örn: 1.5 katıysa 15 puan)
        if vol_avg > 0:
            vol_ratio = vol_now / vol_avg
            vol_puan = min(20, int(vol_ratio * 10)) # Max 20 ile sınırla
        else:
            vol_puan = 0
            
        score += vol_puan
        if vol_puan >= 15: sebepler.append("Hacim: Patlama")
        elif vol_puan < 8: sebepler.append("Hacim: Zayıf")

        # 4. HIZ (ATR) PUANI (Max 15 Puan)
        hiz_yuzdesi = (atr / current_price) * 100
        
        # SÜZGEÇ: Çok hantal (Günde %1.5 altı) hisseleri ele
        if hiz_yuzdesi < 1.5: return None 
        
        # Puan hesabı: %4 hareket 15 tam puan.
        hiz_puan = min(15, int(hiz_yuzdesi * 3.5))
        score += hiz_puan
        
        # 5. MOMENTUM 20 GÜN (Max 10 Puan)
        # Son 20 günde % kaç gitmiş? Her %1 prim için 1 puan.
        if price_20_days_ago > 0:
            prim_20 = ((current_price - price_20_days_ago) / price_20_days_ago) * 100
            mom_puan = min(10, int(prim_20))
            score += mom_puan

        # --- FİNAL KARAR MEKANİZMASI ---
        # Çıtayı yükselttik. Artık 85 altı "Mükemmel" olamaz.
        karar = "BEKLE"
        if score >= 85: karar = "GÜÇLÜ AL"
        elif score >= 65: karar = "AL"
        
        # SÜRE TAHMİNİ (%5 Hedef için)
        gun_tahmini = max(1, int(5 / hiz_yuzdesi))
        vade_str = f"1-{gun_tahmini + 1} Gün"

        analiz_metni = " | ".join(sebepler)
        
        return {
            "karar": karar,
            "guven_skoru": score,
            "analiz_ozeti": analiz_metni,
            "fiyat": round(current_price, 2),
            "rsi": round(rsi, 2),
            "hedef_fiyat": round(current_price * 1.05, 2), # %5 Kar
            "stop_loss": round(current_price * 0.96, 2),   # %4 Stop
            "vade": vade_str,
            "hiz": round(hiz_yuzdesi, 2)
        }
    except:
        return None

# --- ANA MOTOR (FULL LİSTE TARAMA) ---
def run_news_bot():
    print(f"🧠 Sazlık Full Mod: {len(WATCHLIST_TICKERS)} Hisse için GADDAR Analiz Başlıyor...")
    
    all_signals = []
    
    # RASTGELE YOK! LİSTENİN TAMAMI TARANACAK.
    scan_list = WATCHLIST_TICKERS 

    for i, ticker in enumerate(scan_list):
        # Terminalde ilerlemeyi görmek için (Her 20 hissede bir yazar)
        if i % 20 == 0: 
            print(f"⏳ İlerleme: {i}/{len(scan_list)} hisse tarandı...")
            
        try:
            res = garantici_baba_analiz(ticker)
            
            # Sadece 60 puan barajını geçenleri listeye al
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

    # CSV KAYIT (HER SEFERİNDE SIFIRDAN YAZAR)
    if all_signals:
        df = pd.DataFrame(all_signals)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"✅ Tarama Bitti! {len(all_signals)} adet fırsat bulundu.")
        return len(all_signals)
    
    print("❌ Tarama Bitti! Hiçbir hisse kriterlere uyamadı.")
    return 0 

if __name__ == "__main__":
    run_news_bot()
