import yfinance as yf
import pandas as pd
import numpy as np
import config 

# --- 1. MATEMATİKSEL MOTOR (GÜVEN MASASI KALESİ) ---
def calculate_precision_metrics(df):
    if len(df) < 20: return None
    data = df.tail(20).copy()
    y = data['Close'].values
    x = np.arange(len(y))
    
    # Eğim (Slope) ve R2 (Doğrusallık)
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Verimlilik Oranı (Efficiency Ratio - ER)
    direction = abs(y[-1] - y[0])
    volatility = np.sum(np.abs(np.diff(y)))
    er = direction / volatility if volatility != 0 else 0
    
    return slope, r_squared, er

# --- 2. AVCI MOTORU (AMİRAL & GÜVEN AYRIMI) ---
def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Amiral masası için 200 günlük ortalama gerektiğinden 1 yıllık veri çekiyoruz
        df = stock.history(period="1y")
        if df.empty or len(df) < 200: return None

        curr = df['Close'].iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        # Hacim Kontrolü
        vol_current = df['Volume'].tail(5).mean()
        vol_avg = df['Volume'].tail(20).mean()
        vol_factor = vol_current / vol_avg if vol_avg > 0 else 1.0

        if vol_factor >= 1.2: vol_signal = "🔥 GÜÇLÜ YAKIT"
        elif vol_factor >= 0.8: vol_signal = "✅ NORMAL"
        else: vol_signal = "⚠️ DÜŞÜK HACİM"

        # ATR (Dinamik Süren Stop İçin)
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
        atr = df['ATR'].iloc[-1]

        # Güven Masası Metrikleri Hesapla
        res = calculate_precision_metrics(df)
        if not res: return None
        slope, r2, er = res

        sonuc = None

        # ⚓ MASA 1: AMİRAL (Trend Avcısı)
        # Kural: Fiyat SMA200'ün üstünde VE SMA50 > SMA200 (Golden Cross / Büyük Trend)
        if curr > sma200 and sma50 > sma200:
            amiral_score = min(100, 60 + (vol_factor * 15))
            sonuc = {
                "Hisse": ticker, "Fiyat": curr, "Masa": "Amiral",
                "Puan": amiral_score, "Hedef": curr + (atr * 4), "Stop": curr - (atr * 2),
                "Vol_Signal": vol_signal, "Vol_Factor": vol_factor, "Vade": "Dinamik Trend"
            }

        # 🛡️ MASA 2: GÜVEN (İstikrar Kalesi)
        # Kural: Amiral olamasa bile, R2 > 0.65 ise ve trend stabilse buraya girer
        elif slope > 0 and r2 > 0.65 and curr > sma50:
            guven_score = (r2 * 60) + (er * 40)
            if vol_factor < 0.8: guven_score *= 0.90 # Düşük hacim cezası
            
            sonuc = {
                "Hisse": ticker, "Fiyat": curr, "Masa": "Guven",
                "Puan": guven_score, "Hedef": curr + (atr * 2.5), "Stop": curr - (atr * 1.5),
                "Vol_Signal": vol_signal, "Vol_Factor": vol_factor, "Vade": "Uzun Vade"
            }

        return sonuc

    except Exception:
        return None

# --- 3. TARAMA YÖNETİCİSİ (WEB ARAYÜZÜ İÇİN API) ---
def run_analysis_engine():
    ignore = ["PORTFOY", "NAKIT", "TOPLAM"]
    clean_list = [t for t in config.WATCHLIST_TICKERS if t not in ignore]
    
    masa_amiral = []
    masa_guven = []
    
    for ticker in clean_list:
        res = analyze_stock(ticker)
        if res:
            if res["Masa"] == "Amiral":
                masa_amiral.append(res)
            elif res["Masa"] == "Guven":
                masa_guven.append(res)
    
    # Masaları puanlarına göre en iyi 10 hisse olacak şekilde sırala
    masa_guven = sorted(masa_guven, key=lambda x: x['Puan'], reverse=True)[:10]
    masa_amiral = sorted(masa_amiral, key=lambda x: x['Puan'], reverse=True)[:10]
    
    return masa_guven, masa_amiral
