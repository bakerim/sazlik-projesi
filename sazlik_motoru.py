import yfinance as yf
import pandas as pd
import ta
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime

class SazlikAnaliz:
    def __init__(self):
        # Hangi hissede hangi strateji? (Burası projenin beyni)
        self.portfoy = {
            "NVDA": "SUPER_TREND", "META": "SUPER_TREND", "MSFT": "SUPER_TREND",
            "AVGO": "SUPER_TREND", "LLY":  "SUPER_TREND", "TSLA": "SUPER_TREND",
            "KO": "MACD", "PG": "MACD", "JNJ": "MACD", "PEP": "MACD",
            "MCD": "MACD", "WMT": "MACD", "JPM": "MACD", "XOM": "MACD",
            "CVX": "MACD", "CAT": "MACD", "V": "MACD"
        }
        
        # Raporlama klasörü yoksa oluştur
        if not os.path.exists('raporlar'):
            os.makedirs('raporlar')

    def veri_getir(self, symbol):
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            return df
        except:
            return pd.DataFrame()

    def supertrend_hesapla(self, df, period=10, multiplier=3):
        high = df['High']
        low = df['Low']
        close = df['Close']
        atr = ta.volatility.average_true_range(high, low, close, window=period)
        hl2 = (high + low) / 2
        basic_upperband = hl2 + (multiplier * atr)
        basic_lowerband = hl2 - (multiplier * atr)
        
        final_upperband = pd.Series(0.0, index=df.index)
        final_lowerband = pd.Series(0.0, index=df.index)
        supertrend = pd.Series(0.0, index=df.index)
        
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

    def analiz_et(self):
        sonuclar = []
        
        print("Sazlık Motoru çalışıyor... Veriler işleniyor...")
        
        for symbol, strateji in self.portfoy.items():
            df = self.veri_getir(symbol)
            if df.empty or len(df) < 30: continue
            
            fiyat = df['Close'].iloc[-1]
            sinyal = "NÖTR"
            trend = "YATAY"
            aksiyon = "YOK" # Rapor için sadeleştirilmiş çıktı
            
            # --- MACD ---
            if strateji == "MACD":
                macd = ta.trend.MACD(close=df['Close'])
                df['MACD'] = macd.macd()
                df['Signal'] = macd.macd_signal()
                
                bugun_macd = df['MACD'].iloc[-1]
                bugun_sig = df['Signal'].iloc[-1]
                dun_macd = df['MACD'].iloc[-2]
                dun_sig = df['Signal'].iloc[-2]
                
                if bugun_macd > bugun_sig:
                    trend = "YÜKSELİŞ"
                    if dun_macd <= dun_sig:
                        sinyal = "AL"
                        aksiyon = "ALIM FIRSATI"
                        self.grafik_ciz(symbol, df, "MACD", "AL")
                    else:
                        sinyal = "TUT"
                else:
                    trend = "DÜŞÜŞ"
                    if dun_macd >= dun_sig:
                        sinyal = "SAT"
                        aksiyon = "SAT/ÇIK"
                        self.grafik_ciz(symbol, df, "MACD", "SAT")
                    else:
                        sinyal = "NAKİT"

            # --- SUPER TREND ---
            elif strateji == "SUPER_TREND":
                st = self.supertrend_hesapla(df)
                bugun_st = st.iloc[-1]
                dun_st = st.iloc[-2]
                
                if bugun_st == 1:
                    trend = "YÜKSELİŞ"
                    if dun_st == -1:
                        sinyal = "AL"
                        aksiyon = "TREND BAŞLADI"
                        self.grafik_ciz(symbol, df, "SUPER_TREND", "AL")
                    else:
                        sinyal = "TUT"
                else:
                    trend = "DÜŞÜŞ"
                    if dun_st == 1:
                        sinyal = "SAT"
                        aksiyon = "TREND BİTTİ"
                        self.grafik_ciz(symbol, df, "SUPER_TREND", "SAT")
                    else:
                        sinyal = "NAKİT"
            
            sonuclar.append({
                "Tarih": datetime.now().strftime("%Y-%m-%d"),
                "Hisse": symbol,
                "Fiyat": round(fiyat, 2),
                "Strateji": strateji,
                "Trend": trend,
                "Sinyal": sinyal,
                "Aksiyon": aksiyon
            })
            
        return pd.DataFrame(sonuclar)

    def grafik_ciz(self, symbol, df, strateji, yon):
        """Sadece AL/SAT sinyali verenlerin grafiğini çizer ve kaydeder"""
        plt.figure(figsize=(10, 6))
        plt.plot(df.index, df['Close'], label='Fiyat', color='black', alpha=0.5)
        
        if strateji == "MACD":
            plt.title(f"{symbol} - MACD {yon} Sinyali Detayı")
        else:
            plt.title(f"{symbol} - SuperTrend {yon} Sinyali Detayı")
            
        plt.grid(True, alpha=0.3)
        dosya_adi = f"raporlar/{symbol}_{yon}_{datetime.now().strftime('%Y%m%d')}.png"
        plt.savefig(dosya_adi)
        plt.close()

if __name__ == "__main__":
    # Test bloğu
    motor = SazlikAnaliz()
    df_sonuc = motor.analiz_et()
    print(df_sonuc)