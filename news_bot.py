import yfinance as yf
import pandas as pd
import numpy as np
import ta 
import config 

# --- MATEMATİKSEL MOTOR ---
def calculate_precision_metrics(df):
    if len(df) < 20: return None
    data = df.tail(20).copy()
    y = data['Close'].values
    x = np.arange(len(y))
    
    # Eğim (Slope) ve R2
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Verimlilik (ER)
    direction = abs(y[-1] - y[0])
    volatility = np.sum(np.abs(np.diff(y)))
    er = direction / volatility if volatility != 0 else 0
    
    return slope, r_squared, er

# --- HİSSE ANALİZİ ---
def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="3mo")
        if df.empty or len(df) < 30: return None

        # 1. HACİM KONTROLÜ (YENİ)
        # Son 5 günün ortalama hacmi vs. Son 20 günün ortalaması
        vol_current = df['Volume'].tail(5).mean()
        vol_avg = df['Volume'].mean()
        vol_factor = vol_current / vol_avg if vol_avg > 0 else 1.0
        
        if vol_factor >= 1.1: vol_signal = "🔥 GÜÇLÜ YAKIT"
        elif vol_factor >= 0.9: vol_signal = "✅ NORMAL"
        else: vol_signal = "⚠️ DÜŞÜK HACİM"

        # 2. TEKNİK METRİKLER
        res = calculate_precision_metrics(df)
        if not res: return None
        slope, r2, er = res
        curr = df['Close'].iloc[-1]
        
        # Filtre: Düşüş trendindekileri almayalım
        if slope <= 0: return None 

        # --- MASA 1: GÜVEN (İstikrar) ---
        guven_score = (r2 * 60) + (er * 40)
        # Hacim cezası: Eğer hacim düşükse güven puanını kır
        if vol_factor < 0.8: guven_score *= 0.90
        
        # Güven Hedefi (ATR Tabanlı)
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
        atr = df['ATR'].iloc[-1]
        hedef_g = curr + (atr * 2.5)
        stop_g = curr - (atr * 1.5)

        # --- MASA 2: FIRSAT (Hız/Scalp) ---
        hedef_f = curr * 1.05 # Sabit %5
        stop_f = curr * 0.97  # Sabit %3
        
        # Vade Hesabı (Gün)
        vade_gun = (hedef_f - curr) / slope if slope > 0 else 20
        
        # Fırsat Puanı: Hız + Hacim Bonusu
        firsat_score = max(0, 100 - (vade_gun * 8))
        if vol_factor >= 1.2: firsat_score *= 1.10 # Hacimliyse puanı artır
        
        hiz_pct = (slope / curr) * 100

        # Vade Metni
        if vade_gun <= 1.5: vade_str = "⚡ 1 GÜN"
        elif vade_gun <= 3.5: vade_str = "🚀 2-3 GÜN"
        else: vade_str = "📅 4 GÜN+"
        
        return {
            "Hisse": ticker, "Fiyat": curr,
            "Guven_Puan": guven_score, "Firsat_Puan": firsat_score,
            "R2": r2, "ER": er, "Slope": slope,
            "Vade": vade_str, "Hiz_Pct": hiz_pct,
            "Vol_Signal": vol_signal, "Vol_Factor": vol_factor,
            "Hedef_G": hedef_g, "Stop_G": stop_g,
            "Hedef_F": hedef_f, "Stop_F": stop_f
        }
    except Exception:
        return None

# --- TARAMA YÖNETİCİSİ ---
def run_analysis_engine():
    ignore = ["PORTFOY", "NAKIT", "TOPLAM"]
    clean_list = [t for t in config.WATCHLIST_TICKERS if t not in ignore]
    
    all_results = []
    for ticker in clean_list:
        res = analyze_stock(ticker)
        if res: all_results.append(res)
    
    # Masa 1: Güven Listesi (R2 > 0.65 ve ER makul)
    masa_guven = sorted([r for r in all_results if r['R2'] > 0.65], key=lambda x: x['Guven_Puan'], reverse=True)[:6]
    
    # Masa 2: Fırsat Listesi (En yüksek Fırsat Puanı)
    masa_firsat = sorted(all_results, key=lambda x: x['Firsat_Puan'], reverse=True)[:6]
    
    return masa_guven, masa_firsat