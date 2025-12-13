import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import numpy as np
from datetime import datetime
import warnings

# Uyarıları sustur
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- SADECE ELİT HİSSELER ---
TEST_TICKERS = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "AAPL", 
    "AMD", "NFLX", "PLTR", "COST", "LLY", "JPM", "SMCI", "MSTR", "COIN"
]

BASLANGIC_KASA = 1000.0   
ISLEM_BASI_YUZDE = 0.50   # Kasanın %50'si (2 Hisse)
# YENİ KURALLAR:
ILK_KAR_AL_YUZDE = 0.10   # %10 kâr görünce yarısını sat (Win Rate'i artırır)
TRAILING_STOP_YUZDE = 0.10 # Kalanı için izleyen stop
KOMISYON = 1.5            
VERGI_ORANI = 0.15        

# --- SNIPER BARON SKORLAMA ---
def sinyal_kontrol(row):
    try:
        close = float(row['Close'])
        sma20 = float(row['SMA_20'])
        sma50 = float(row['SMA_50'])
        sma200 = float(row['SMA_200'])
        rsi = float(row['RSI_14'])
    except: return "YOK"

    # FİLTRE: Trend Yukarı
    if close < sma200 or close < sma50: return "YOK"
    if rsi < 55: return "YOK"

    # GİRİŞ: Momentum Kırılımı
    if close > sma20:
        return "AL"
    
    return "YOK"

def main():
    print("\n" + "="*60)
    print(f"🔫 GARANTİCİ BABA v11.0 - SNIPER BARON")
    print(f"🔥 Hedef: %10'da Yarısını Sat, Kalanıyla Ralliye Katıl")
    print(f"💰 Kasa: ${BASLANGIC_KASA} | 🍰 Pozisyon: %{ISLEM_BASI_YUZDE*100}")
    print("="*60)

    # 1. VERİLERİ HAZIRLA
    print("⏳ Veriler işleniyor...")
    market_data = {}
    tum_tarihler = set()

    for t in TEST_TICKERS:
        try:
            df = yf.download(t, period="2y", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if len(df) > 200:
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
    # Portföy yapısı: 'yarisi_satildi_mi': False eklendi
    portfoy = {} 
    islem_gecmisi = []
    toplam_komisyon = 0
    
    for gun in zaman_cizelgesi:
        # A. DEĞERLEME
        portfoy_degeri = nakit
        for t, poz in portfoy.items():
            if gun in market_data[t].index:
                curr = market_data[t].loc[gun]['Close']
                portfoy_degeri += poz['adet'] * curr
            else:
                portfoy_degeri += poz['adet'] * poz['zirve_fiyat']

        # B. SATIŞ KONTROLÜ
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            curr = row['Close']
            high = row['High']
            low = row['Low']
            
            # Zirveyi Güncelle
            if high > poz['zirve_fiyat']:
                poz['zirve_fiyat'] = high
            
            sebeb = ""
            cikis_fiyati = 0
            satilan_adet = 0
            
            # 1. ERKEN HASAT (Kar Al - %10)
            # Eğer henüz yarısını satmadıysak ve fiyat %10 arttıysa
            if not poz['yarisi_satildi_mi'] and high >= poz['maliyet'] * (1 + ILK_KAR_AL_YUZDE):
                cikis_fiyati = poz['maliyet'] * (1 + ILK_KAR_AL_YUZDE)
                satilan_adet = poz['adet'] / 2 # Yarısını sat
                sebeb = "İLK KAR AL (%10)"
                
                # Portföyü güncelle (Kalan yarısı devam ediyor)
                poz['adet'] -= satilan_adet
                poz['yarisi_satildi_mi'] = True
                poz['stop_seviyesi'] = poz['maliyet'] # Kalanın stopunu girişe çek (Risk=0)
                
                # Nakit girişi
                satis_tutari = satilan_adet * cikis_fiyati
                brut = satis_tutari - (satilan_adet * poz['maliyet'])
                vergi = brut * VERGI_ORANI
                net = brut - KOMISYON - vergi
                nakit += satis_tutari - KOMISYON - vergi
                toplam_komisyon += KOMISYON
                
                islem_gecmisi.append({
                    'Hisse': t,
                    'Tarih': gun.date(),
                    'Net Kar': round(net, 2),
                    'Yüzde': round((net / (satilan_adet * poz['maliyet'])) * 100, 2),
                    'Sebep': sebeb
                })
                continue # Döngüye devam (Hisseden tamamen çıkmadık)

            # 2. TAMAMEN ÇIKIŞ (Trailing Stop veya Stop Loss)
            # Eğer yarısı satıldıysa stop seviyemiz Maliyettir (Risk Free)
            # Satılmadıysa normal Trailing Stop işler
            
            if poz['yarisi_satildi_mi']:
                # Zirveden %10 düşerse VEYA Maliyetin altına inerse sat
                stop_level = max(poz['maliyet'], poz['zirve_fiyat'] * (1 - TRAILING_STOP_YUZDE))
            else:
                # Normal Trailing Stop
                stop_level = poz['zirve_fiyat'] * (1 - TRAILING_STOP_YUZDE)
            
            if low <= stop_level:
                cikis_fiyati = stop_level
                satilan_adet = poz['adet']
                sebeb = "STOP / TRAILING"
                
                # Komple Satış
                satis_tutari = satilan_adet * cikis_fiyati
                brut = satis_tutari - (satilan_adet * poz['maliyet'])
                vergi = brut * VERGI_ORANI if brut > 0 else 0
                net = brut - KOMISYON - vergi
                nakit += satis_tutari - KOMISYON - vergi
                toplam_komisyon += KOMISYON
                
                islem_gecmisi.append({
                    'Hisse': t,
                    'Tarih': gun.date(),
                    'Net Kar': round(net, 2),
                    'Yüzde': round((net / (satilan_adet * poz['maliyet'])) * 100, 2),
                    'Sebep': sebeb
                })
                satilacaklar.append(t)
        
        for t in satilacaklar: del portfoy[t]
            
        # C. ALIŞ
        bos_yer = 2 - len(portfoy)
        if bos_yer > 0 and nakit > 100: 
            adaylar = []
            for t in TEST_TICKERS:
                if t in portfoy: continue 
                if t not in market_data: continue
                if gun not in market_data[t].index: continue
                
                row = market_data[t].loc[gun]
                if sinyal_kontrol(row) == "AL":
                    adaylar.append((t, row['RSI_14']))
            
            adaylar.sort(key=lambda x: x[1], reverse=True)
            
            for t, rsi in adaylar[:bos_yer]:
                hedef_tutar = portfoy_degeri * ISLEM_BASI_YUZDE
                if hedef_tutar > nakit: hedef_tutar = nakit - KOMISYON - 5
                if hedef_tutar < 100: continue
                
                row = market_data[t].loc[gun]
                fiyat = row['Close']
                adet = hedef_tutar / fiyat
                
                nakit -= (adet * fiyat + KOMISYON)
                toplam_komisyon += KOMISYON
                
                portfoy[t] = {
                    'adet': adet, 
                    'maliyet': fiyat, 
                    'tarih': gun,
                    'zirve_fiyat': fiyat,
                    'yarisi_satildi_mi': False # Yeni özellik
                }

    # --- SONUÇLAR ---
    son_deger = nakit
    for t, poz in portfoy.items():
        if not market_data[t].empty:
            son_deger += poz['adet'] * market_data[t].iloc[-1]['Close']
            
    print("\n" + "-"*30)
    print("📊 SNIPER BARON SONUÇLARI")
    print("-" * 30)
    print(f"Bitiş          : ${son_deger:.2f}")
    kar_zarar = son_deger - BASLANGIC_KASA
    print(f"Net Kar/Zarar  : ${kar_zarar:.2f} (%{kar_zarar/BASLANGIC_KASA*100:.2f})")
    print(f"💸 Komisyon      : ${toplam_komisyon:.2f}")
    
    if islem_gecmisi:
        df = pd.DataFrame(islem_gecmisi)
        win = len(df[df['Net Kar'] > 0])
        print(f"Başarı Oranı   : %{(win/len(df))*100:.1f} (Hedef: %50+)")
        print(f"Toplam İşlem   : {len(df)}")
        print("\n🏆 SON İŞLEMLER:")
        print(df.sort_values('Tarih', ascending=False).head(5)[['Hisse', 'Tarih', 'Net Kar', 'Sebep']].to_string(index=False))

if __name__ == "__main__":
    main()