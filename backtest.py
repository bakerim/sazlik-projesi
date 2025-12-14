import yfinance as yf
import pandas as pd
import numpy as np

# --- AYARLAR ---
TEST_TICKERS = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "PLTR", "MSTR", "COIN"
]

BASLANGIC_KASA = 250.0    
GIRIS_GUCU = 0.98         # %98 All-In
KOMISYON = 1.0            # İşlem başı komisyon

# --- HEDEF SEVİYELERİ ---
TARGET_1_PCT = 0.10  # %10 Kar
TARGET_2_PCT = 0.30  # %30 Kar
TARGET_3_PCT = 0.50  # %50 Kar
STOP_LOSS_PCT = 0.08 # %8 Stop

# --- ÖZEL MATEMATİK MOTORU (Kütüphanesiz) ---
def add_indicators(df):
    # 1. SMA Hesaplama
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    # 2. RSI Hesaplama (Wilder's RSI)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    return df

def main():
    print("\n" + "="*70)
    print(f"🧪 SNIPER ELITE - 3 KADEMELİ ROKET TESTİ (BAĞIMSIZ MOTOR)")
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
                df = add_indicators(df) # Kendi fonksiyonumuzla hesapla
                market_data[t] = df
                tum_tarihler.update(df.index)
        except Exception as e:
            # print(f"Hata {t}: {e}") 
            continue

    zaman_cizelgesi = sorted(list(tum_tarihler))
    
    # 2. SİMÜLASYON DEĞİŞKENLERİ
    nakit = BASLANGIC_KASA
    portfoy = {} 
    islem_gecmisi = []
    
    istatistik = {
        "Stop Olanlar": 0,
        "Hedef 1 (Güvenlik)": 0,
        "Hedef 2 (Trend)": 0,
        "Hedef 3 (Jackpot)": 0
    }

    # 3. ZAMAN MAKİNESİ
    for gun in zaman_cizelgesi:
        # A. MEVCUT POZİSYONLARI YÖNET
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            high = row['High']
            low = row['Low']
            
            # STOP KONTROLÜ
            if low <= poz['stop']:
                satis_fiyati = poz['stop']
                gelir = poz['adet'] * satis_fiyati - KOMISYON
                nakit += gelir
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': t, 'Olay': 'STOP LOSS', 'Fiyat': satis_fiyati, 'Kasa': nakit})
                satilacaklar.append(t)
                istatistik["Stop Olanlar"] += 1
                continue

            # HEDEF 1 (%10)
            if not poz['t1_ok'] and high >= poz['maliyet'] * (1 + TARGET_1_PCT):
                satilacak_adet = poz['adet'] / 2
                satis_fiyati = poz['maliyet'] * (1 + TARGET_1_PCT)
                nakit += (satilacak_adet * satis_fiyati) - KOMISYON
                poz['adet'] -= satilacak_adet
                poz['t1_ok'] = True
                poz['stop'] = poz['maliyet'] # Stop Maliyete Çekildi
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': t, 'Olay': '🎯 HEDEF 1', 'Fiyat': satis_fiyati, 'Kasa': nakit})
                istatistik["Hedef 1 (Güvenlik)"] += 1

            # HEDEF 2 (%30)
            if poz['t1_ok'] and not poz['t2_ok'] and high >= poz['maliyet'] * (1 + TARGET_2_PCT):
                satilacak_adet = poz['adet'] / 2
                satis_fiyati = poz['maliyet'] * (1 + TARGET_2_PCT)
                nakit += (satilacak_adet * satis_fiyati) - KOMISYON
                poz['adet'] -= satilacak_adet
                poz['t2_ok'] = True
                poz['stop'] = poz['maliyet'] * (1 + TARGET_1_PCT) # Stop Kar Al 1'e Çekildi
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': t, 'Olay': '🚀 HEDEF 2', 'Fiyat': satis_fiyati, 'Kasa': nakit})
                istatistik["Hedef 2 (Trend)"] += 1
                
            # HEDEF 3 (%50)
            if poz['t2_ok'] and high >= poz['maliyet'] * (1 + TARGET_3_PCT):
                satis_fiyati = poz['maliyet'] * (1 + TARGET_3_PCT)
                gelir = poz['adet'] * satis_fiyati - KOMISYON
                nakit += gelir
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': t, 'Olay': '💰 JACKPOT', 'Fiyat': satis_fiyati, 'Kasa': nakit})
                satilacaklar.append(t)
                istatistik["Hedef 3 (Jackpot)"] += 1
        
        for t in satilacaklar: del portfoy[t]

        # B. YENİ ALIM
        if len(portfoy) == 0 and nakit > 50:
            adaylar = []
            for t in TEST_TICKERS:
                if t not in market_data or gun not in market_data[t].index: continue
                row = market_data[t].loc[gun]
                try:
                    # SNIPER STRATEJİSİ
                    sma200 = row['SMA_200']
                    sma50 = row['SMA_50']
                    sma20 = row['SMA_20']
                    rsi = row['RSI_14']
                    close = row['Close']
                    
                    if pd.isna(sma200) or pd.isna(rsi): continue # Veri yoksa geç

                    if (close > sma200 and close > sma50) and (rsi >= 55) and (close > sma20):
                        adaylar.append((t, rsi))
                except: continue
            
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
                islem_gecmisi.append({'Tarih': gun.date(), 'Hisse': secilen, 'Olay': 'ALIM', 'Fiyat': fiyat, 'Kasa': nakit})

    # --- SONUÇLAR ---
    son_deger = nakit
    for t, poz in portfoy.items():
        curr = market_data[t].iloc[-1]['Close']
        son_deger += poz['adet'] * curr

    kar_zarar = son_deger - BASLANGIC_KASA
    yuzde = (kar_zarar / BASLANGIC_KASA) * 100

    print("-" * 50)
    print(f"📊 SONUÇ TABLOSU")
    print("-" * 50)
    print(f"Bitiş Kasası     : ${son_deger:.2f}")
    print(f"Net Getiri       : ${kar_zarar:.2f} (%{yuzde:.2f})")
    print("-" * 50)
    print(f"✅ Hedef 1 (%10) Yakalanan : {istatistik['Hedef 1 (Güvenlik)']}")
    print(f"🚀 Hedef 2 (%30) Yakalan