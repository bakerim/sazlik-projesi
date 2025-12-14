import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- AYARLAR ---
# Sadece "Özel Tim" (En yüksek volatilite ve momentum)
TEST_TICKERS = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "PLTR", "MSTR", "COIN"
]

BASLANGIC_KASA = 250.0    
GIRIS_GUCU = 0.98         # %98 All-In
KOMISYON = 1.0            # İşlem başı komisyon (Alım/Satım)

# --- HEDEF SEVİYELERİ ---
TARGET_1_PCT = 0.10  # %10 Kar (Pozisyonun %50'si satılır)
TARGET_2_PCT = 0.30  # %30 Kar (Kalanın %50'si satılır)
TARGET_3_PCT = 0.50  # %50 Kar (Jackpot - Hepsi satılır)
STOP_LOSS_PCT = 0.08 # %8 Stop

def main():
    print("\n" + "="*70)
    print(f"🧪 SNIPER ELITE - 3 KADEMELİ ROKET TESTİ")
    print(f"💰 Kasa: ${BASLANGIC_KASA} | 🎯 Hedefler: %10 / %30 / %50")
    print("="*70)

    # 1. VERİLERİ HAZIRLA
    print("⏳ Veriler işleniyor (Son 2 Yıl)...")
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

    zaman_cizelgesi = sorted(list(tum_tarihler))
    
    # 2. SİMÜLASYON DEĞİŞKENLERİ
    nakit = BASLANGIC_KASA
    portfoy = {}  # { 'Hisse': {'adet': 10, 'maliyet': 100, 't1_ok': False, 't2_ok': False, 'stop': 92} }
    islem_gecmisi = []
    
    istatistik = {
        "Stop Olanlar": 0,
        "Hedef 1 (Güvenlik)": 0,
        "Hedef 2 (Trend)": 0,
        "Hedef 3 (Jackpot)": 0
    }

    # 3. ZAMAN MAKİNESİ
    for gun in zaman_cizelgesi:
        # A. MEVCUT POZİSYONLARI YÖNET (SATIŞ SİMÜLASYONU)
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            high = row['High']
            low = row['Low']
            close = row['Close']
            
            # 1. STOP KONTROLÜ
            if low <= poz['stop']:
                # Stop Patladı - Hepsini Sat
                satis_fiyati = poz['stop']
                gelir = poz['adet'] * satis_fiyati - KOMISYON
                nakit += gelir
                
                net_kar = gelir - (poz['adet'] * poz['maliyet_orijinal']) # Sadece bu parçanın karı değil, toplam işlem matematiği karışık, basit tutalım.
                
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': t, 'Olay': 'STOP LOSS', 'Fiyat': satis_fiyati})
                satilacaklar.append(t)
                istatistik["Stop Olanlar"] += 1
                continue

            # 2. HEDEF 1 KONTROLÜ (%10)
            if not poz['t1_ok'] and high >= poz['maliyet'] * (1 + TARGET_1_PCT):
                # Yarısını Sat
                satilacak_adet = poz['adet'] / 2
                satis_fiyati = poz['maliyet'] * (1 + TARGET_1_PCT)
                
                nakit += (satilacak_adet * satis_fiyati) - KOMISYON
                
                # Pozisyonu Güncelle
                poz['adet'] -= satilacak_adet
                poz['t1_ok'] = True
                poz['stop'] = poz['maliyet'] # STOP'U MALİYETE ÇEK (Risk Free)
                
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': t, 'Olay': '🎯 HEDEF 1 (%10)', 'Fiyat': satis_fiyati})
                istatistik["Hedef 1 (Güvenlik)"] += 1

            # 3. HEDEF 2 KONTROLÜ (%30)
            if poz['t1_ok'] and not poz['t2_ok'] and high >= poz['maliyet'] * (1 + TARGET_2_PCT):
                # Kalanın Yarısını Sat (Yani başlangıcın %25'i)
                satilacak_adet = poz['adet'] / 2
                satis_fiyati = poz['maliyet'] * (1 + TARGET_2_PCT)
                
                nakit += (satilacak_adet * satis_fiyati) - KOMISYON
                
                poz['adet'] -= satilacak_adet
                poz['t2_ok'] = True
                # Stop'u Hedef 1 seviyesine çek (Kar Kilitle)
                poz['stop'] = poz['maliyet'] * (1 + TARGET_1_PCT)
                
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': t, 'Olay': '🚀 HEDEF 2 (%30)', 'Fiyat': satis_fiyati})
                istatistik["Hedef 2 (Trend)"] += 1
                
            # 4. HEDEF 3 (JACKPOT) KONTROLÜ (%50)
            if poz['t2_ok'] and high >= poz['maliyet'] * (1 + TARGET_3_PCT):
                # Kalan Hepsini Sat
                satis_fiyati = poz['maliyet'] * (1 + TARGET_3_PCT)
                gelir = poz['adet'] * satis_fiyati - KOMISYON
                nakit += gelir
                
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': t, 'Olay': '💰 JACKPOT (%50+)', 'Fiyat': satis_fiyati})
                satilacaklar.append(t) # Pozisyon bitti
                istatistik["Hedef 3 (Jackpot)"] += 1
        
        # Listeden silinecekleri temizle
        for t in satilacaklar: del portfoy[t]

        # B. YENİ ALIM (Eğer Nakit Varsa ve Pozisyon Yoksa)
        if len(portfoy) == 0 and nakit > 50:
            adaylar = []
            for t in TEST_TICKERS:
                if t not in market_data or gun not in market_data[t].index: continue
                row = market_data[t].loc[gun]
                
                # SNIPER STRATEJİSİ
                try:
                    sma200 = row['SMA_200']
                    sma50 = row['SMA_50']
                    sma20 = row['SMA_20']
                    rsi = row['RSI_14']
                    close = row['Close']
                    
                    if (close > sma200 and close > sma50) and (rsi >= 55) and (close > sma20):
                        adaylar.append((t, rsi))
                except: continue
            
            # En yüksek RSI olanı seç
            adaylar.sort(key=lambda x: x[1], reverse=True)
            
            if adaylar:
                secilen = adaylar[0][0]
                row = market_data[secilen].loc[gun]
                fiyat = row['Close']
                
                alincak_tutar = nakit * GIRIS_GUCU
                adet = alincak_tutar / fiyat
                
                nakit -= (alincak_tutar + KOMISYON)
                
                portfoy[secilen] = {
                    'adet': adet,
                    'maliyet': fiyat,
                    'maliyet_orijinal': fiyat,
                    'stop': fiyat * (1 - STOP_LOSS_PCT),
                    't1_ok': False,
                    't2_ok': False
                }
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': secilen, 'Olay': 'ALIM', 'Fiyat': fiyat})

    # --- RAPORLAMA ---
    # Son gün portföy değeri
    son_deger = nakit
    for t, poz in portfoy.items():
        curr = market_data[t].iloc[-1]['Close']
        son_deger += poz['adet'] * curr

    kar_zarar = son_deger - BASLANGIC_KASA
    yuzde = (kar_zarar / BASLANGIC_KASA) * 100

    print("-" * 40)
    print("📊 LABORATUVAR SONUCU")
    print("-" * 40)
    print(f"Başlangıç Kasası : ${BASLANGIC_KASA}")
    print(f"Bitiş Kasası     : ${son_deger:.2f}")
    print(f"Net Kar/Zarar    : ${kar_zarar:.2f} (%{yuzde:.2f})")
    print("-" * 40)
    print("📈 İSTATİSTİKLER (Kademeli Satış Başarısı)")
    print(f"❌ Stop Olan İşlemler    : {istatistik['Stop Olanlar']}")
    print(f"✅ Hedef 1 (%10) Kilit   : {istatistik['Hedef 1 (Güvenlik)']}")
    print(f"🚀 Hedef 2 (%30) Trend   : {istatistik['Hedef 2 (Trend)']}")
    print(f"💰 Hedef 3 (%50) Jackpot : {istatistik['Hedef 3 (Jackpot)']}")
    print("-" * 40)
    
    # Son 10 İşlem
    print("\n📜 SON OPERASYON KAYITLARI:")
    df_log = pd.DataFrame(islem_gecmisi)
    if not df_log.empty:
        print(df_log.tail(10).to_string(index=False))

if __name__ == "__main__":
    main()