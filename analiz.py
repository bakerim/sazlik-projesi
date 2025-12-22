import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import numpy as np

# İncelemek istediğin hisseyi buraya yaz
SYMBOL = "PEP"  # Robotun SAT dediği hisse
STRATEGY = "MACD" # Bu hisse için kullanılan strateji (Robot listesinden bak)

print(f"{SYMBOL} için detaylı grafik hazırlanıyor...")

# Veri Çek
df = yf.download(SYMBOL, period="6mo", interval="1d", progress=False, auto_adjust=True)
if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)

plt.figure(figsize=(14, 8))

# --- MACD ANALİZİ ---
if STRATEGY == "MACD":
    # Göstergeler
    macd = ta.trend.MACD(close=df['Close'])
    df['MACD'] = macd.macd()
    df['Signal'] = macd.macd_signal()
    
    # Üst Grafik: Fiyat
    plt.subplot(2, 1, 1)
    plt.plot(df.index, df['Close'], label='Fiyat', color='black', alpha=0.6)
    plt.title(f'{SYMBOL} - Fiyat Hareketi')
    plt.grid(True, alpha=0.3)
    plt.legend()

    # Alt Grafik: MACD Kesişimi
    plt.subplot(2, 1, 2)
    plt.plot(df.index, df['MACD'], label='MACD (Mavi)', color='blue')
    plt.plot(df.index, df['Signal'], label='Sinyal Hattı (Kırmızı)', color='red', linestyle='--')
    
    # Kesişim Noktalarını İşaretle
    # SAT Sinyali: Mavi çizgi Kırmızı çizginin altına düştüğü an
    satis_sinyalleri = (df['MACD'] < df['Signal']) & (df['MACD'].shift(1) >= df['Signal'].shift(1))
    alim_sinyalleri = (df['MACD'] > df['Signal']) & (df['MACD'].shift(1) <= df['Signal'].shift(1))
    
    # Grafiğe Ok Ekleme
    son_satis_tarihi = df[satis_sinyalleri].index[-1]
    plt.annotate('SAT SİNYALİ', 
                 xy=(son_satis_tarihi, df.loc[son_satis_tarihi, 'MACD']), 
                 xytext=(son_satis_tarihi, df.loc[son_satis_tarihi, 'MACD'] + 1),
                 arrowprops=dict(facecolor='red', shrink=0.05))

    plt.title(f'{SYMBOL} - MACD Kesişimi (Neden SAT Verdi?)')
    plt.grid(True, alpha=0.3)
    plt.legend()

# --- SUPER TREND ANALİZİ ---
elif STRATEGY == "SUPER_TREND":
    # (SuperTrend fonksiyonu buraya eklenebilir ama şu an PEP MACD olduğu için gerek yok)
    pass

plt.tight_layout()
plt.savefig("analiz_sonuc.png")
print(f"Grafik 'analiz_sonuc.png' olarak kaydedildi. Açıp bakabilirsin!")