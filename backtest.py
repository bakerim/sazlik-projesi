import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import numpy as np
from datetime import datetime
import warnings

# Uyarıları sustur
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- AYARLAR ---
TEST_TICKERS = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "PLTR", "MSTR", "COIN"
]

BASLANGIC_KASA = 250.0    
ISLEM_BASI_YUZDE = 0.98   # %98 ALL-IN (Bileşik Getiriyi iliklerine kadar hissetmek için)
ILK_KAR_AL_YUZDE = 0.10   
TRAILING_STOP_YUZDE = 0.10 
KOMISYON = 1.5            
VERGI_ORANI = 0.15        

# --- STRATEJİ MOTORU ---
def sinyal_kontrol(row):
    try:
        close = float(row['Close'])
        sma20 = float(row['SMA_20'])
        sma50 = float(row['SMA_50'])
        sma200 = float(row['SMA_200'])
        rsi = float(row['RSI_14'])
    except: return "YOK"

    if pd.notna(sma200) and close < sma200: return "YOK"
    if close < sma50: return "YOK"
    if rsi < 55: return "YOK"

    if close > sma20:
        return "AL"
    return "YOK"

def main():
    print("\n" + "="*70)
    print(f"☃️ 250$ DENEYİ v13.0 - KAR TOPU (BİLEŞİK GETİRİ)")
    print(f"💰 Kasa: ${BASLANGIC_KASA} | 🚀 Giriş Gücü: %{ISLEM_BASI_YUZDE*100}")
    print(f"📉 Felsefe: Kazandığını tekrar yatır, mermiyi büyüt.")
    print("="*70)

    # 1. VERİLERİ HAZIRLA
    print("⏳ Veriler işleniyor...")
    market_data = {}
    tum_tarihler = set()

    for t in TEST_TICKERS:
        try:
            df = yf.download(t, period="2y", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if len(df) > 50: 
                df.ta.rsi(length=14, append=True)
                df.ta.sma(length=20, append=True)
                df.ta.sma(length=50, append=True)
                df.ta.sma(length=200, append=True)
                market_data[t] = df
                tum_tarihler.update(df.index)
        except: continue

    if not market_data: return
    zaman_cizelgesi = sorted(list(tum_tarihler))
    
    # 2. SİMÜLASYON
    nakit = BASLANGIC_KASA
    portfoy = {} 
    islem_gecmisi = []
    equity_curve = [] 
    toplam_komisyon = 0
    
    ilk_islem_buyuklugu = 0
    son_islem_buyuklugu = 0
    
    for gun in zaman_cizelgesi:
        # A. DEĞERLEME
        portfoy_degeri = nakit
        for t, poz in portfoy.items():
            if gun in market_data[t].index:
                curr = market_data[t].loc[gun]['Close']
                portfoy_degeri += poz['adet'] * curr
            else:
                portfoy_degeri += poz['adet'] * poz['zirve_fiyat']
        
        equity_curve.append(portfoy_degeri)

        # B. SATIŞ
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            high = row['High']
            low = row['Low']
            
            if high > poz['zirve_fiyat']: poz['zirve_fiyat'] = high
            
            sebeb = ""
            cikis_fiyati = 0
            satilan_adet = 0
            
            # DURUM 1: İLK KAR AL (%10)
            if not poz['yarisi_satildi_mi'] and high >= poz['maliyet'] * (1 + ILK_KAR_AL_YUZDE):
                cikis_fiyati = poz['maliyet'] * (1 + ILK_KAR_AL_YUZDE)
                satilan_adet = poz['adet'] / 2 
                sebeb = "İLK KAR AL (%10)"
                
                poz['adet'] -= satilan_adet
                poz['yarisi_satildi_mi'] = True
                poz['stop_seviyesi'] = poz['maliyet'] 
                
                satis_tutari = satilan_adet * cikis_fiyati
                brut = satis_tutari - (satilan_adet * poz['maliyet'])
                vergi = brut * VERGI_ORANI
                net = brut - KOMISYON - vergi
                nakit += satis_tutari - KOMISYON - vergi
                toplam_komisyon += KOMISYON
                
                islem_gecmisi.append({
                    'Hisse': t, 'Tarih': gun.date(), 'Net Kar': round(net, 2),
                    'İşlem Hacmi': round(satilan_adet * poz['maliyet'], 2),
                    'Sebep': sebeb
                })
                continue 

            # DURUM 2: KOMPLE ÇIKIŞ
            if poz['yarisi_satildi_mi']:
                stop_level = max(poz['maliyet'], poz['zirve_fiyat'] * (1 - TRAILING_STOP_YUZDE))
            else:
                stop_level = poz['zirve_fiyat'] * (1 - TRAILING_STOP_YUZDE)
            
            if low <= stop_level:
                cikis_fiyati = stop_level
                satilan_adet = poz['adet']
                sebeb = "STOP / TRAILING"
                
                satis_tutari = satilan_adet * cikis_fiyati
                brut = satis_tutari - (satilan_adet * poz['maliyet'])
                vergi = brut * VERGI_ORANI if brut > 0 else 0
                net = brut - KOMISYON - vergi
                nakit += satis_tutari - KOMISYON - vergi
                toplam_komisyon += KOMISYON
                
                islem_gecmisi.append({
                    'Hisse': t, 'Tarih': gun.date(), 'Net Kar': round(net, 2),
                    'İşlem Hacmi': round(satilan_adet * poz['maliyet'], 2),
                    'Sebep': sebeb
                })
                satilacaklar.append(t)
        
        for t in satilacaklar: del portfoy[t]
            
        # C. ALIŞ (BİLEŞİK GETİRİ BURADA ÇALIŞIR)
        if len(portfoy) == 0 and nakit > 50: 
            adaylar = []
            for t in TEST_TICKERS:
                if t not in market_data: continue
                if gun not in market_data[t].index: continue
                
                row = market_data[t].loc[gun]
                if sinyal_kontrol(row) == "AL":
                    adaylar.append((t, row['RSI_14']))
            
            adaylar.sort(key=lambda x: x[1], reverse=True)
            
            if adaylar:
                t_secilen = adaylar[0][0]
                
                # BİLEŞİK GETİRİ FORMÜLÜ:
                # Kasa büyüdükçe, işlem büyüklüğü de büyür.
                hedef_tutar = nakit * ISLEM_BASI_YUZDE 
                if hedef_tutar < 50: continue 

                row = market_data[t_secilen].loc[gun]
                fiyat = row['Close']
                adet = hedef_tutar / fiyat
                
                # İstatistik için kaydet
                if ilk_islem_buyuklugu == 0: ilk_islem_buyuklugu = hedef_tutar
                son_islem_buyuklugu = hedef_tutar

                nakit -= (adet * fiyat + KOMISYON)
                toplam_komisyon += KOMISYON
                
                portfoy[t_secilen] = {
                    'adet': adet, 'maliyet': fiyat, 'tarih': gun,
                    'zirve_fiyat': fiyat, 'yarisi_satildi_mi': False
                }

    # --- RAPOR ---
    son_deger = equity_curve[-1]
    kar_zarar = son_deger - BASLANGIC_KASA
    
    # Max Drawdown
    peak = equity_curve[0]
    max_drawdown = 0
    for val in equity_curve:
        if val > peak: peak = val
        dd = (peak - val) / peak
        if dd > max_drawdown: max_drawdown = dd

    print("-" * 40)
    print("📊 KAR TOPU (BİLEŞİK GETİRİ) SONUÇLARI")
    print("-" * 40)
    print(f"Bitiş Kasası     : ${son_deger:.2f}")
    print(f"Net Kar/Zarar    : ${kar_zarar:.2f} (%{kar_zarar/BASLANGIC_KASA*100:.2f})")
    print(f"Ödenen Komisyon  : ${toplam_komisyon:.2f}")
    print("-" * 40)
    print(f"❄️ KAR TOPU ETKİSİ:")
    print(f"İlk Mermi Büyüklüğü : ${ilk_islem_buyuklugu:.2f}")
    print(f"Son Mermi Büyüklüğü : ${son_islem_buyuklugu:.2f}")
    degisim = ((son_islem_buyuklugu - ilk_islem_buyuklugu) / ilk_islem_buyuklugu) * 100
    print(f"Mermi Büyümesi      : %{degisim:.2f}")
    
    if islem_gecmisi:
        df = pd.DataFrame(islem_gecmisi)
        win = len(df[df['Net Kar'] > 0])
        print(f"Başarı Oranı     : %{(win/len(df))*100:.1f}")
        print("\n🏆 SON İŞLEMLER:")
        print(df.sort_values('Tarih', ascending=False).head(5)[['Hisse', 'Tarih', 'İşlem Hacmi', 'Net Kar']].to_string(index=False))

if __name__ == "__main__":
    main()