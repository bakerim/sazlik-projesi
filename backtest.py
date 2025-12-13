import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import numpy as np
from datetime import datetime
import warnings

# Gereksiz uyarıları sustur
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- AYARLAR ---
# Sadece Hacimli ve Trend Yapan "Elit" Hisseler
TEST_TICKERS = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "AAPL", 
    "AMD", "NFLX", "PLTR", "COST", "LLY", "JPM", "SMCI", "MSTR", "COIN"
]

BASLANGIC_KASA = 1000.0   
ISLEM_BASI_YUZDE = 0.50    # Kasanın %50'si (Sadece 2 işlem taşır - Komisyonu ezmek için)
ILK_KAR_AL_YUZDE = 0.10    # %10 kârı görünce yarısını sat (Cebi ısıt)
TRAILING_STOP_YUZDE = 0.10 # Kalanı için zirveden %10 düşüşü takip et (Trendi sağ)
KOMISYON = 1.5             # İşlem başı maliyet
VERGI_ORANI = 0.15         # Kar üzerinden vergi

# --- STRATEJİ MOTORU ---
def sinyal_kontrol(row):
    try:
        close = float(row['Close'])
        sma20 = float(row['SMA_20'])
        sma50 = float(row['SMA_50'])
        sma200 = float(row['SMA_200'])
        rsi = float(row['RSI_14'])
    except: return "YOK"

    # 1. FİLTRE: Fiyat Ana Trendlerin Üzerinde Olmalı (Boğa Piyasası)
    # Eğer SMA200 verisi yoksa (yeni halka arz veya veri eksik), SMA50'ye bak.
    if pd.notna(sma200) and close < sma200: return "YOK"
    if close < sma50: return "YOK"
    
    # 2. FİLTRE: Momentum Güçlü Olmalı (Ölü hisse istemiyoruz)
    if rsi < 55: return "YOK"

    # 3. GİRİŞ SİNYALİ: Kısa Vadeli Düzeltme Bitişi
    # Fiyatın SMA 20'nin üzerine atması "Yola devam" işaretidir.
    if close > sma20:
        return "AL"
    
    return "YOK"

def main():
    print("\n" + "="*70)
    print(f"🔬 GARANTİCİ BABA v12.0 - SNIPER BARON (DETAYLI RÖNTGEN)")
    print(f"💰 Kasa: ${BASLANGIC_KASA} | 🍰 Pozisyon: %{ISLEM_BASI_YUZDE*100} (Max 2 Hisse)")
    print(f"🎯 Strateji: %10'da Yarısını Sat -> Kalanı Trailing Stop ile Sür")
    print("="*70)

    # 1. VERİLERİ HAZIRLA
    print("⏳ Veriler indiriliyor ve işleniyor (Son 2 Yıl)...")
    market_data = {}
    tum_tarihler = set()

    for t in TEST_TICKERS:
        try:
            # period="2y" -> Son 2 yılın verisi (Dinamik)
            df = yf.download(t, period="2y", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if len(df) > 50: # En az 50 gün veri olsun
                df.ta.rsi(length=14, append=True)
                df.ta.sma(length=20, append=True)
                df.ta.sma(length=50, append=True)
                df.ta.sma(length=200, append=True)
                market_data[t] = df
                tum_tarihler.update(df.index)
        except: continue

    if not market_data: 
        print("❌ Veri çekilemedi.")
        return

    zaman_cizelgesi = sorted(list(tum_tarihler))
    print(f"✅ Test Aralığı: {zaman_cizelgesi[0].date()} -> {zaman_cizelgesi[-1].date()}\n")
    
    # 2. SİMÜLASYON BAŞLIYOR
    nakit = BASLANGIC_KASA
    portfoy = {} 
    islem_gecmisi = []
    equity_curve = [] # Günlük kasa değerleri (Drawdown hesabı için)
    toplam_komisyon = 0
    
    for gun in zaman_cizelgesi:
        # A. PORTFÖY DEĞERİNİ HESAPLA
        portfoy_degeri = nakit
        for t, poz in portfoy.items():
            if gun in market_data[t].index:
                curr = market_data[t].loc[gun]['Close']
                portfoy_degeri += poz['adet'] * curr
            else:
                portfoy_degeri += poz['adet'] * poz['zirve_fiyat']
        
        equity_curve.append(portfoy_degeri)

        # B. SATIŞ KONTROLÜ (ÇIKIŞ STRATEJİSİ)
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            high = row['High']
            low = row['Low']
            
            # Zirveyi güncelle (Trailing Stop için)
            if high > poz['zirve_fiyat']:
                poz['zirve_fiyat'] = high
            
            sebeb = ""
            cikis_fiyati = 0
            satilan_adet = 0
            tarih_fark = (gun - poz['tarih']).days
            
            # DURUM 1: İLK KAR AL (%10) - Sadece henüz yarısı satılmadıysa
            if not poz['yarisi_satildi_mi'] and high >= poz['maliyet'] * (1 + ILK_KAR_AL_YUZDE):
                cikis_fiyati = poz['maliyet'] * (1 + ILK_KAR_AL_YUZDE)
                satilan_adet = poz['adet'] / 2 # Yarısını sat
                sebeb = "İLK KAR AL (%10)"
                
                # Portföyü güncelle
                poz['adet'] -= satilan_adet
                poz['yarisi_satildi_mi'] = True
                poz['stop_seviyesi'] = poz['maliyet'] # Kalanın stopunu girişe çek (Risk-Free)
                
                # Nakit işlemi
                satis_tutari = satilan_adet * cikis_fiyati
                brut = satis_tutari - (satilan_adet * poz['maliyet'])
                vergi = brut * VERGI_ORANI
                net = brut - KOMISYON - vergi
                nakit += satis_tutari - KOMISYON - vergi
                toplam_komisyon += KOMISYON
                
                islem_gecmisi.append({
                    'Hisse': t, 'Tarih': gun.date(), 'Net Kar': round(net, 2),
                    'Yüzde': round((net / (satilan_adet * poz['maliyet'])) * 100, 2),
                    'Sebep': sebeb, 'Süre': tarih_fark
                })
                continue # Hissenin kalanı devam ediyor

            # DURUM 2: KOMPLE ÇIKIŞ (Trailing Stop veya Stop Loss)
            if poz['yarisi_satildi_mi']:
                # Yarısı satıldıysa, stop seviyesi ya Maliyettir ya da Zirveden %10 aşağısıdır (Hangisi yüksekse)
                stop_level = max(poz['maliyet'], poz['zirve_fiyat'] * (1 - TRAILING_STOP_YUZDE))
            else:
                # Hiç satılmadıysa normal Trailing Stop
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
                    'Yüzde': round((net / (satilan_adet * poz['maliyet'])) * 100, 2),
                    'Sebep': sebeb, 'Süre': tarih_fark
                })
                satilacaklar.append(t)
        
        for t in satilacaklar: del portfoy[t]
            
        # C. YENİ ALIŞ (GİRİŞ STRATEJİSİ)
        bos_yer = 2 - len(portfoy) # Max 2 hisse kuralı
        if bos_yer > 0 and nakit > 100: 
            adaylar = []
            for t in TEST_TICKERS:
                if t in portfoy: continue 
                if t not in market_data: continue
                if gun not in market_data[t].index: continue
                
                row = market_data[t].loc[gun]
                if sinyal_kontrol(row) == "AL":
                    # RSI'ı yüksek olanı (daha güçlü trendi) önceliklendir
                    adaylar.append((t, row['RSI_14']))
            
            adaylar.sort(key=lambda x: x[1], reverse=True)
            
            for t, rsi in adaylar[:bos_yer]:
                hedef_tutar = portfoy_degeri * ISLEM_BASI_YUZDE
                # Kasada yeterli nakit var mı?
                if hedef_tutar > nakit: hedef_tutar = nakit - KOMISYON - 5
                if hedef_tutar < 100: continue
                
                row = market_data[t].loc[gun]
                fiyat = row['Close']
                adet = hedef_tutar / fiyat
                
                nakit -= (adet * fiyat + KOMISYON)
                toplam_komisyon += KOMISYON
                
                portfoy[t] = {
                    'adet': adet, 'maliyet': fiyat, 'tarih': gun,
                    'zirve_fiyat': fiyat, 'yarisi_satildi_mi': False
                }

    # --- 3. RAPORLAMA VE DETAYLI ANALİZ ---
    son_deger = equity_curve[-1]
    kar_zarar = son_deger - BASLANGIC_KASA
    
    # Max Drawdown (En büyük tepeden düşüş)
    peak = equity_curve[0]
    max_drawdown = 0
    for val in equity_curve:
        if val > peak: peak = val
        dd = (peak - val) / peak
        if dd > max_drawdown: max_drawdown = dd

    print("-" * 40)
    print("📊 PERFORMANS KARNESİ")
    print("-" * 40)
    print(f"Bitiş Kasası     : ${son_deger:.2f}")
    print(f"Toplam Net Kar   : ${kar_zarar:.2f} (%{kar_zarar/BASLANGIC_KASA*100:.2f})")
    print(f"Max Drawdown     : %{max_drawdown*100:.2f} (Riski gösterir)")
    print(f"Ödenen Komisyon  : ${toplam_komisyon:.2f}")
    
    if islem_gecmisi:
        df = pd.DataFrame(islem_gecmisi)
        win_trades = df[df['Net Kar'] > 0]
        loss_trades = df[df['Net Kar'] <= 0]
        
        print("\n📈 İŞLEM İSTATİSTİKLERİ")
        print(f"Toplam İşlem     : {len(df)}")
        print(f"Başarı Oranı     : %{(len(win_trades)/len(df))*100:.1f} (Hedef: %50+)")
        
        avg_win = win_trades['Net Kar'].mean() if not win_trades.empty else 0
        avg_loss = loss_trades['Net Kar'].mean() if not loss_trades.empty else 0
        print(f"Ortalama Kazanç  : ${avg_win:.2f}")
        print(f"Ortalama Kayıp   : ${avg_loss:.2f}")

        print("\n⏳ SÜRE İSTATİSTİKLERİ")
        print(f"En Uzun Tutma    : {df['Süre'].max()} Gün")
        print(f"En Kısa Tutma    : {df['Süre'].min()} Gün")
        print(f"Ortalama Süre    : {df['Süre'].mean():.1f} Gün")

        print("\n🧠 KARAR MEKANİZMASI (ÇIKIŞ SEBEPLERİ)")
        print(df['Sebep'].value_counts().to_string())

        print("\n🏆 EN İYİ 3 İŞLEM (BALİNALAR):")
        print(df.sort_values('Net Kar', ascending=False).head(3)[['Hisse', 'Tarih', 'Net Kar', 'Yüzde', 'Sebep']].to_string(index=False))
        
        print("\n💀 EN KÖTÜ 3 İŞLEM (STOPLAR):")
        print(df.sort_values('Net Kar', ascending=True).head(3)[['Hisse', 'Tarih', 'Net Kar', 'Yüzde', 'Sebep']].to_string(index=False))

    if islem_gecmisi:
        pd.DataFrame(islem_gecmisi).to_csv("backtest_detay.csv", index=False)
        print("\n💾 Detaylı veriler 'backtest_detay.csv' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()