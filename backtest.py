import yfinance as yf
import pandas as pd
import ta
import numpy as np
import warnings

# Gereksiz uyarıları kapat
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

# --- 1. PORTFÖY VE STRATEJİ TANIMLARI ---
# Hangi hissede hangi stratejiyi kullanacağımızı baştan tanımlıyoruz.
portfoy = {
    # AGRESIF (Roketler) -> SuperTrend Kullan
    "NVDA": "SUPER_TREND",
    "META": "SUPER_TREND",
    "MSFT": "SUPER_TREND",
    "AVGO": "SUPER_TREND",
    "LLY":  "SUPER_TREND",
    "TSLA": "SUPER_TREND",
    
    # DEFANSIF (Kaleler) -> MACD Kullan
    "KO":   "MACD",
    "PG":   "MACD",
    "JNJ":  "MACD",
    "PEP":  "MACD",
    "MCD":  "MACD",
    "WMT":  "MACD",
    
    # DÖNGÜSEL (Bankalar/Enerji) -> MACD Kullan
    "JPM":  "MACD",
    "XOM":  "MACD",
    "CVX":  "MACD",
    "CAT":  "MACD",
    "V":    "MACD"
}

# --- 2. YARDIMCI FONKSİYONLAR ---

def calculate_supertrend(df, period=10, multiplier=3):
    """SuperTrend İndikatörü Hesaplama"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    atr = ta.volatility.average_true_range(high, low, close, window=period)
    hl2 = (high + low) / 2
    basic_upperband = hl2 + (multiplier * atr)
    basic_lowerband = hl2 - (multiplier * atr)
    
    final_upperband = pd.Series(0.0, index=df.index)
    final_lowerband = pd.Series(0.0, index=df.index)
    supertrend = pd.Series(0.0, index=df.index) # 1: UP, -1: DOWN
    
    for i in range(1, len(df.index)):
        if basic_upperband.iloc[i] < final_upperband.iloc[i-1] or close.iloc[i-1] > final_upperband.iloc[i-1]:
            final_upperband.iloc[i] = basic_upperband.iloc[i]
        else:
            final_upperband.iloc[i] = final_upperband.iloc[i-1]
            
        if basic_lowerband.iloc[i] > final_lowerband.iloc[i-1] or close.iloc[i-1] < final_lowerband.iloc[i-1]:
            final_lowerband.iloc[i] = basic_lowerband.iloc[i]
        else:
            final_lowerband.iloc[i] = final_lowerband.iloc[i-1]
            
        if supertrend.iloc[i-1] == 1:
            if close.iloc[i] < final_lowerband.iloc[i]:
                supertrend.iloc[i] = -1
            else:
                supertrend.iloc[i] = 1
        else:
            if close.iloc[i] > final_upperband.iloc[i]:
                supertrend.iloc[i] = 1
            else:
                supertrend.iloc[i] = -1
                
    return supertrend

def get_market_data(symbol):
    """Son 6 aylık veriyi çeker"""
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        return df
    except:
        return pd.DataFrame()

# --- 3. ROBOT ANA DÖNGÜSÜ ---

print("\n🤖 SAZLIK SİNYAL ROBOTU ÇALIŞIYOR...")
print("Piyasa verileri analiz ediliyor, lütfen bekleyin...\n")

print("-" * 95)
print(f"{'HİSSE':<8} | {'FİYAT':<10} | {'STRATEJİ':<12} | {'TREND YÖNÜ':<15} | {'SİNYAL (AKSIYON)':<20}")
print("-" * 95)

for symbol, strategy_type in portfoy.items():
    df = get_market_data(symbol)
    
    if df.empty or len(df) < 30:
        continue
        
    current_price = df['Close'].iloc[-1]
    trend_yonu = "NÖTR"
    sinyal = "BEKLE"
    renk = "\033[0m" # Default

    # --- STRATEJİ A: MACD ---
    if strategy_type == "MACD":
        macd = ta.trend.MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()
        
        # Son gün değerleri
        bugun_macd = df['MACD'].iloc[-1]
        bugun_signal = df['Signal'].iloc[-1]
        dun_macd = df['MACD'].iloc[-2]
        dun_signal = df['Signal'].iloc[-2]
        
        # Trend Belirleme
        if bugun_macd > bugun_signal:
            trend_yonu = "YUKARI 🟢"
            # Kesişim Kontrolü (Yeni mi kesti?)
            if dun_macd <= dun_signal:
                sinyal = "AL (YENİ SİNYAL) 🚀"
                renk = "\033[92m" # Parlak Yeşil
            else:
                sinyal = "TUT (Yükseliş Sürüyor)"
                renk = "\033[94m" # Mavi
        else:
            trend_yonu = "AŞAĞI 🔴"
            if dun_macd >= dun_signal:
                sinyal = "SAT (YENİ SİNYAL) 🔻"
                renk = "\033[91m" # Kırmızı
            else:
                sinyal = "NAKİTTE KAL"
                renk = "\033[90m" # Gri

    # --- STRATEJİ B: SUPER TREND ---
    elif strategy_type == "SUPER_TREND":
        st = calculate_supertrend(df)
        df['SuperTrend'] = st
        
        bugun_st = df['SuperTrend'].iloc[-1]
        dun_st = df['SuperTrend'].iloc[-2]
        
        if bugun_st == 1:
            trend_yonu = "YUKARI 🟢"
            if dun_st == -1:
                sinyal = "AL (Trend Başladı) 🚀"
                renk = "\033[92m"
            else:
                sinyal = "TUT (Ralli Devam)"
                renk = "\033[94m"
        else:
            trend_yonu = "AŞAĞI 🔴"
            if dun_st == 1:
                sinyal = "SAT (Trend Bitti) 🔻"
                renk = "\033[91m"
            else:
                sinyal = "NAKİTTE KAL"
                renk = "\033[90m"

    # Satırı Yazdır
    reset = "\033[0m"
    print(f"{symbol:<8} | ${current_price:<9.2f} | {strategy_type:<12} | {trend_yonu:<15} | {renk}{sinyal:<20}{reset}")

print("-" * 95)
print("ℹ️ NOT: 'YENİ SİNYAL' yazanlar bugün veya dün aksiyon gerektirenlerdir.")
print("ℹ️ 'TUT' veya 'NAKİTTE KAL' mevcut pozisyonu koru demektir.")