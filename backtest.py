import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import time
from datetime import datetime

# --- AYARLAR ---
# Test edilecek hisseler (Hem teknoloji hem defansif karışık)
TEST_TICKERS = [
    "AAPL", "TSLA", "NVDA", "AMD", "AMZN", "GOOGL", "META", 
    "JPM", "KO", "XOM", "PFE", "T", "F", "INTC", "PLTR"
]

BASLANGIC_BAKIYE = 10000  # 10.000$ ile başlıyoruz
STOP_LOSS = 0.05          # %5 Zarar Kes
TAKE_PROFIT = 0.15        # %15 Kar Al (Trendi sürmek için biraz geniş tuttuk)
TEST_SURESI_YIL = 2       # Son 2 yılı test et

def skor_hesapla(row):
    """Garantici Baba Algoritmasının Birebir Aynısı"""
    score = 50
    
    rsi = row['RSI_14']
    close = row['Close']
    sma50 = row['SMA_50']
    sma200 = row['SMA_200']
    
    if pd.isna(rsi) or pd.isna(sma200): return 0

    # 1. RSI
    if rsi < 30: score += 25
    elif rsi < 40: score += 10
    elif rsi > 70: score -= 20
    
    # 2. Trend (SMA 200)
    if close > sma200: score += 15
    else: score -= 10
        
    # 3. Golden Cross
    if sma50 > sma200: score += 10
    
    # 4. Momentum (Fiyat vs SMA50)
    if close > sma50: score += 5
        
    return score

def backtest_motoru(ticker):
    print(f"⏳ {ticker} simüle ediliyor...", end=" ")
    
    # Veri Çekme
    try:
        df = yf.download(ticker, period=f"{TEST_SURESI_YIL}y", interval="1d", progress=False)
        if len(df) < 200: 
            print("❌ Yetersiz Veri")
            return None
    except:
        print("❌ Veri Hatası")
        return None

    # Veriyi Temizle (Multi-index sorununu çöz)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # İndikatörler
    df.ta.rsi(length=14, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    
    # Simülasyon Değişkenleri
    pozisyon = False
    giris_fiyati = 0
    giris_tarihi = None
    bakiye = BASLANGIC_BAKIYE
    islem_gecmisi = []
    
    # GÜN GÜN İLERLE
    # İlk 200 gün indikatörlerin oturması için atlanır
    for i in range(200, len(df)):
        gun = df.index[i]
        row = df.iloc[i]
        
        fiyat = float(row['Close'])
        yuksek = float(row['High'])
        dusuk = float(row['Low'])
        
        # Puan Hesapla
        puan = skor_hesapla(row)
        
        # --- ÇIKIŞ STRATEJİSİ ---
        if pozisyon:
            kar_orani = (fiyat - giris_fiyati) / giris_fiyati
            
            sebeb = ""
            cikis_fiyati = 0
            
            # 1. Stop Loss
            if dusuk <= giris_fiyati * (1 - STOP_LOSS):
                cikis_fiyati = giris_fiyati * (1 - STOP_LOSS)
                sebeb = "STOP LOSS"
            # 2. Take Profit
            elif yuksek >= giris_fiyati * (1 + TAKE_PROFIT):
                cikis_fiyati = giris_fiyati * (1 + TAKE_PROFIT)
                sebeb = "KAR AL"
            # 3. Trend Bozuldu (Puan Düştü)
            elif puan <= 40: 
                cikis_fiyati = fiyat
                sebeb = "TEKNİK BOZULMA"
            
            if sebeb:
                kar_tutar = (cikis_fiyati - giris_fiyati) * (bakiye / giris_fiyati) # Basit hesap
                # Bakiyeyi güncelle (Bileşik getiri simülasyonu için)
                # bakiye = bakiye * (cikis_fiyati / giris_fiyati) 
                
                gercek_kar_yuzde = ((cikis_fiyati - giris_fiyati) / giris_fiyati) * 100
                
                islem_gecmisi.append({
                    'Hisse': ticker,
                    'Alış': giris_tarihi.date(),
                    'Satış': gun.date(),
                    'Giriş': round(giris_fiyati, 2),
                    'Çıkış': round(cikis_fiyati, 2),
                    'Kar %': round(gercek_kar_yuzde, 2),
                    'Sebep': sebeb
                })
                pozisyon = False
                continue

        # --- GİRİŞ STRATEJİSİ ---
        if not pozisyon:
            # Puan 60 üstüyse AL
            if puan >= 60:
                pozisyon = True
                giris_fiyati = fiyat
                giris_tarihi = gun
    
    # Hisse Getirisi (Buy & Hold)
    ilk_fiyat = df['Close'].iloc[200]
    son_fiyat = df['Close'].iloc[-1]
    bh_getiri = ((son_fiyat - ilk_fiyat) / ilk_fiyat) * 100
    
    print(f"✅ Bitti ({len(islem_gecmisi)} İşlem)")
    return islem_gecmisi, bh_getiri

def main():
    print("\n" + "="*60)
    print(f"🛡️  GARANTİCİ BABA - BACKTEST RAPORU ({TEST_SURESI_YIL} YIL)")
    print("="*60)
    
    tum_islemler = []
    bh_kiyaslama = {}
    
    for hisse in TEST_TICKERS:
        sonuc = backtest_motoru(hisse)
        if sonuc:
            islemler, bh_getiri = sonuc
            tum_islemler.extend(islemler)
            bh_kiyaslama[hisse] = bh_getiri
            
    if not tum_islemler:
        print("❌ Hiç işlem yapılmadı.")
        return

    df_res = pd.DataFrame(tum_islemler)
    
    # --- İSTATİSTİKLER ---
    toplam_islem = len(df_res)
    karli = df_res[df_res['Kar %'] > 0]
    zararli = df_res[df_res['Kar %'] <= 0]
    
    win_rate = (len(karli) / toplam_islem) * 100
    avg_return = df_res['Kar %'].mean()
    total_return = df_res['Kar %'].sum() # Basit kümülatif
    
    print("\n" + "-"*30)
    print("📊 GENEL PERFORMANS")
    print("-"*30)
    print(f"Toplam İşlem     : {toplam_islem}")
    print(f"Başarı Oranı     : %{win_rate:.1f}")
    print(f"Ortalama Getiri  : %{avg_return:.2f} (İşlem Başı)")
    print(f"Toplam Getiri    : %{total_return:.2f} (Basit Toplam)")
    
    print("\n🏆 EN İYİ 3 İŞLEM:")
    print(df_res.sort_values('Kar %', ascending=False).head(3)[['Hisse', 'Alış', 'Kar %', 'Sebep']].to_string(index=False))
    
    print("\n💀 EN KÖTÜ 3 İŞLEM:")
    print(df_res.sort_values('Kar %', ascending=True).head(3)[['Hisse', 'Alış', 'Kar %', 'Sebep']].to_string(index=False))
    
    # Kaydet
    df_res.to_csv("backtest_sonuc.csv", index=False)
    print("\n💾 Detaylı döküm 'backtest_sonuc.csv' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()
