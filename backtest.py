import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import numpy as np
from datetime import datetime
import warnings

# Uyarıları sustur
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- SADECE ELİT HİSSELER (ÖLÜLERİ ATTIK) ---
TEST_TICKERS = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "AAPL", # Muhteşem 7'li + Broadcom
    "AMD", "NFLX", "PLTR", "COST", "LLY", "JPM", "SMCI", "MSTR", "COIN" # Yüksek Momentum
]

BASLANGIC_KASA = 1000.0   
ISLEM_BASI_YUZDE = 0.50   # DİKKAT: Kasanın %50'si (Sadece 2 Hisse). Komisyonu ezmek için şart.
TRAILING_STOP_YUZDE = 0.12 # Zirveden %12 düşerse sat (Geniş alan bırak, trendde kal)
TEST_SURESI_YIL = 2       
KOMISYON = 1.5            
VERGI_ORANI = 0.15        

# --- TREND BARONU SKORLAMA ---
def sinyal_kontrol(row):
    try:
        close = float(row['Close'])
        sma20 = float(row['SMA_20'])
        sma50 = float(row['SMA_50'])
        sma200 = float(row['SMA_200'])
        rsi = float(row['RSI_14'])
    except: return "YOK"

    # FİLTRE 1: KESİN TREND (Fiyat 200 ve 50 günlüğün üzerinde olacak)
    if close < sma200 or close < sma50: return "YOK"

    # FİLTRE 2: MOMENTUM GÜCÜ (RSI 55 üstü olmalı, trend güçlü demek)
    if rsi < 55: return "YOK"

    # GİRİŞ SİNYALİ:
    # Fiyat kısa vadeli ortalamayı (SMA 20) yukarı kırdıysa veya üzerinde tutunuyorsa
    # Bu "Düzeltme bitti, ralli devam ediyor" demektir.
    if close > sma20:
        return "AL"
    
    return "YOK"

def main():
    print("\n" + "="*60)
    print(f"🎩 GARANTİCİ BABA v10.0 - TREND BARONU")
    print(f"🔥 Felsefe: Az İşlem, Büyük Oyna, Trendi Sağ")
    print(f"💰 Kasa: ${BASLANGIC_KASA} | 🍰 Pozisyon: %{ISLEM_BASI_YUZDE*100} (Max 2 Hisse)")
    print("="*60)

    # 1. VERİLERİ HAZIRLA
    print("⏳ Elit hisseler taranıyor...")
    market_data = {}
    tum_tarihler = set()

    for t in TEST_TICKERS:
        try:
            df = yf.download(t, period=f"{TEST_SURESI_YIL}y", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if len(df) > 200:
                # İNDİKATÖRLER
                df.ta.rsi(length=14, append=True)
                df.ta.sma(length=20, append=True)  # Kısa Vade (Tetik)
                df.ta.sma(length=50, append=True)  # Orta Vade (Trend)
                df.ta.sma(length=200, append=True) # Uzun Vade (Filtre)
                
                market_data[t] = df
                tum_tarihler.update(df.index)
        except: continue

    if not market_data: return
    zaman_cizelgesi = sorted(list(tum_tarihler))
    
    # 2. SİMÜLASYON
    nakit = BASLANGIC_KASA
    portfoy = {} 
    islem_gecmisi = []
    toplam_komisyon = 0
    
    for gun in zaman_cizelgesi:
        # A. PORTFÖY DEĞERLEME
        portfoy_degeri = nakit
        for t, poz in portfoy.items():
            if gun in market_data[t].index:
                curr = market_data[t].loc[gun]['Close']
                portfoy_degeri += poz['adet'] * curr
            else:
                portfoy_degeri += poz['adet'] * poz['zirve_fiyat']

        # B. SATIŞ (TRAILING STOP)
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            curr = row['Close']
            high = row['High']
            
            # Zirveyi Güncelle
            if high > poz['zirve_fiyat']:
                poz['zirve_fiyat'] = high
            
            # Trailing Stop Kontrolü
            stop_level = poz['zirve_fiyat'] * (1 - TRAILING_STOP_YUZDE)
            
            sebeb = ""
            cikis_fiyati = 0
            
            if row['Low'] <= stop_level:
                cikis_fiyati = stop_level # Stop tetiklendi
                sebeb = "TRAILING STOP"
            
            # Trend Tamamen Bozulursa (SMA 50 altı kapanış - Acil Çıkış)
            elif curr < row['SMA_50']:
                cikis_fiyati = curr
                sebeb = "TREND ÇÖKÜŞÜ (SMA 50)"

            if sebeb:
                satis_tutari = poz['adet'] * cikis_fiyati
                brut = satis_tutari - (poz['adet'] * poz['maliyet'])
                
                vergi = brut * VERGI_ORANI if brut > 0 else 0
                net = brut - KOMISYON - vergi
                nakit += satis_tutari - KOMISYON - vergi
                toplam_komisyon += KOMISYON
                
                days_held = (gun - poz['tarih']).days
                
                islem_gecmisi.append({
                    'Hisse': t,
                    'Tarih': gun.date(),
                    'Net Kar': round(net, 2),
                    'Yüzde': round((net / (poz['adet'] * poz['maliyet'])) * 100, 2),
                    'Süre': days_held,
                    'Sebep': sebeb
                })
                satilacaklar.append(t)
        
        for t in satilacaklar: del portfoy[t]
            
        # C. ALIŞ (TREND BARONU GİRİŞİ)
        # Sadece elimizde nakit varsa ve portföy dolu değilse (Max 2 hisse)
        # Portföy değeri üzerinden %50 hesaplıyoruz
        
        bos_yer = 2 - len(portfoy) # Max 2 hisse
        if bos_yer > 0 and nakit > 100: 
            
            # Adayları Bul
            adaylar = []
            for t in TEST_TICKERS:
                if t in portfoy: continue 
                if t not in market_data: continue
                if gun not in market_data[t].index: continue
                
                row = market_data[t].loc[gun]
                if sinyal_kontrol(row) == "AL":
                    # RSI'ı yüksek olanı (daha güçlü trendi) öne alalım
                    adaylar.append((t, row['RSI_14']))
            
            # RSI'a göre sırala (En güçlü momentum)
            adaylar.sort(key=lambda x: x[1], reverse=True)
            
            # Alım Yap
            for t, rsi in adaylar[:bos_yer]:
                hedef_tutar = portfoy_degeri * ISLEM_BASI_YUZDE
                # Kasadaki paradan fazla alamaz
                if hedef_tutar > nakit: hedef_tutar = nakit - KOMISYON - 5 # 5 dolar güvenlik payı
                
                if hedef_tutar < 100: continue # Çok küçük bakiye kaldıysa alma
                
                row = market_data[t].loc[gun]
                fiyat = row['Close']
                adet = hedef_tutar / fiyat
                
                nakit -= (adet * fiyat + KOMISYON)
                toplam_komisyon += KOMISYON
                
                portfoy[t] = {
                    'adet': adet, 
                    'maliyet': fiyat, 
                    'tarih': gun,
                    'zirve_fiyat': fiyat
                }

    # --- RAPOR ---
    son_deger = nakit
    for t, poz in portfoy.items():
        if not market_data[t].empty:
            son_deger += poz['adet'] * market_data[t].iloc[-1]['Close']
            
    print("\n" + "-"*30)
    print("📊 TREND BARONU SONUÇLARI")
    print("-" * 30)
    print(f"Başlangıç      : ${BASLANGIC_KASA:.2f}")
    print(f"Bitiş          : ${son_deger:.2f}")
    kar_zarar = son_deger - BASLANGIC_KASA
    yuzde = (kar_zarar/BASLANGIC_KASA)*100
    print(f"Net Kar/Zarar  : ${kar_zarar:.2f} (%{yuzde:.2f})")
    print(f"💸 Komisyon      : ${toplam_komisyon:.2f}")
    
    if islem_gecmisi:
        df = pd.DataFrame(islem_gecmisi)
        win = len(df[df['Net Kar'] > 0])
        print(f"Başarı Oranı   : %{(win/len(df))*100:.1f}")
        print(f"Toplam İşlem   : {len(df)}")
        print(f"Ort. Süre      : {df['Süre'].mean():.1f} Gün")
        print("\n🏆 EFSANE İŞLEMLER:")
        print(df.sort_values('Net Kar', ascending=False).head(5)[['Hisse', 'Tarih', 'Net Kar', 'Yüzde', 'Süre']].to_string(index=False))

    if islem_gecmisi:
        pd.DataFrame(islem_gecmisi).to_csv("backtest_portfoy.csv", index=False)

if __name__ == "__main__":
    main()