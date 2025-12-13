import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import numpy as np
from datetime import datetime
import warnings

# Uyarıları temizle
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- AYARLAR ---
# Piranha, hareketsiz hisseyi sevmez. Sadece Oynak (Volatil) Hisseler:
TEST_TICKERS = [
 "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE", 
    "CRM", "CMCSA", "QCOM", "TXN", "AMGN", "INTC", "CSCO", "VZ", "T", "TMUS",
    "NFLX", "ORCL", "MU", "IBM", "PYPL", "INTU", "AMD", "FTNT", "ADI", "NOW",
    "LRCX", "MRVL", "CDNS", "SNPS", "DXCM", "KLAC", "ROST", "ANSS", "MSCI", "CHTR",
    
    # --- FİNANS & FİNANSAL HİZMETLER ---
    "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPY", "BLK", "SCHW",
    "C", "AXP", "CB", "MMC", "AON", "CME", "ICE", "PGR", "ALL", "MET",
    "AIG", "PNC", "USB", "BK", "COF", "DFS", "TRV", "MCO", "CBOE", "RJF",
    "GPN", "FIS", "ZION", "FITB", "STT", "NDAQ", "RF", "KEY", "CFG", "HBAN",
    
    # --- SAĞLIK & İLAÇ ---
    "JNJ", "LLY", "UNH", "ABBV", "MRK", "PFE", "DHR", "TMO", "MDT", "SYK",
    "AMGN", "GILD", "BIIB", "VRTX", "BMY", "ISRG", "ABT", "ZTS", "BDX", "BSX",
    "CI", "CVS", "HUM", "HCA", "ANTM", "LH", "COO", "ALGN", "HOLX", "DVA",
    "WAT", "RGEN", "IQV", "REGN", "EW", "TECH", "PKI", "DGX", "INCY", "CRL",
    
    # --- TEMEL TÜKETİM & DAYANIKLI TÜKETİM (İstikrar) ---
    "PG", "KO", "PEP", "WMT", "COST", "HD", "MCD", "NKE", "LOW", "TGT",
    "SBUX", "MDLZ", "CL", "PM", "MO", "KR", "DG", "ADBE", "EL", "KHC",
    "GIS", "K", "SYY", "APO", "DECK", "BBY", "WHR", "NWSA", "FOXA", "HAS",
    "MAT", "HOG", "GT", "TIF", "TPR", "TTC", "VFC", "HBI", "KSS", "ULTA",
    
    # --- ENERJİ & SANAYİ (Köklü Şirketler) ---
    "XOM", "CVX", "BRK.B", "LMT", "RTX", "BA", "HON", "MMM", "GE", "GD",
    "CAT", "DE", "EOG", "OXY", "SLB", "COP", "PSX", "MPC", "WMB", "KMI",
    "ETN", "AOS", "EMR", "PCAR", "ROK", "SWK", "TDY", "RSG", "WM", "CARR",
    "ITW", "GWW", "WAB", "IEX", "AAL", "DAL", "UAL", "LUV", "HA", "ALK",
    
    # --- EMLAK, KAMU HİZMETLERİ & DİĞER (Çeşitlilik) ---
    "DUK", "NEE", "SO", "EXC", "AEP", "SRE", "WEC", "D", "ED", "XEL",
    "VNQ", "SPG", "PLD", "EQIX", "AMT", "CCI", "HST", "O", "ARE", "PSA",
    "WY", "BXP", "REG", "VTR", "AVB", "ESR", "EPR", "KIM", "FRT", "APTS",
    "LUMN", "VIAC", "FOX", "DISCA", "ETSY", "EBAY", "ATVI", "EA", "TTWO", "ZG"

    # --- YARI İLETKEN & BULUT BİLİŞİM ---
    "ASML", "AMAT", "TSM", "MCHP", "TER", "U", "VEEV", "OKTA", "NET", "CRWD", 
    "DDOG", "ZS", "TEAM", "ADSK", "MSI", "FTV", "WDC", "ZBRA", "SWKS", "QDEL",

    # --- YENİLENEBİLİR ENERJİ & EV (Elektrikli Araçlar) ---
    "FSLY", "PLUG", "ENPH", "SEDG", "RUN", "SPWR", "BLDP", "FCEL", "BE", "SOL",
    "LI", "NIO", "XPEV", "RIVN", "LCID", "NKLA", "WKHS", "QS", "ARVL", "GOEV",

    # --- FİNANSAL TEKNOLOJİ (FinTech) & Dijital Ödeme ---
    "SQ", "COIN", "HOOD", "UPST", "AFRM", "SOFI", "MQ", "BILL", "TOST", "PAYA",
    "DWAC", "BRZE", "AVLR", "DOCU", "SABR", "TTEC", "TWLO", "RNG", "ZM", "COUP",
    
    # --- BİYOTEKNOLOJİ & SAĞLIK (Yüksek Büyüme) ---
    "MRNA", "PFE", "BIIB", "VRTX", "REGN", "GILD", "AMGN", "BMRN", "ALXN", "CTAS",
    "CORT", "EXEL", "IONS", "XBI", "LABU", "EDIT", "BEAM", "NTLA", "CRSP", "ALLK",

    # --- E-TİCARET & YENİ MEDYA ---
    "MELI", "ETSY", "ROKU", "PTON", "SPOT", "CHWY", "ZM", "DOCU", "DDOG", "FVRR",
    "PINS", "SNAP", "TWTR", "WIX", "SHOP", "SE", "BABA", "JD", "BIDU", "PDD",

    # --- ENDÜSTRİ & OTOMASYON (Orta Ölçekli ve Dinamik) ---
    "ROP", "TT", "Ametek", "FLR", "HUBB", "APH", "ECL", "SHW", "PPG", "FMC",
    "MOS", "CF", "NUE", "STLD", "ALK", "AAL", "DAL", "LUV", "UAL", "SAVE",
    "CAR", "RCL", "CCL", "NCLH", "MGM", "WYNN", "LVS", "PENN", "DKNG", "BYND",

    # --- ÇEŞİTLİ DİNAMİK BÜYÜME (Mid-Cap/IPO) ---
    "RBLX", "UBER", "LYFT", "ABNB", "DOX", "GPN", "FLT", "PRU", "MET", "L",
    "VLO", "PSX", "MPC", "DVN", "APA", "MRO", "EOG", "OXY", "SLB", "HAL",
    "BKR", "FTI", "NOV", "TDW", "PAGP", "ENLC", "PAA", "WES", "WMB", "KMI",
    "ETN", "AOS", "EMR", "PCAR", "ROK", "SWK", "TDY", "RSG", "WM", "CARR"
]

BASLANGIC_KASA = 1000.0   
ISLEM_BASI_YUZDE = 0.20   # Kasanın %20'si (200$ ile giriş - Komisyonu ezmek için)
STOP_LOSS = 0.15          # %15 (RSI 2 stratejisinde stop geniştir, çünkü düşeni alıyoruz)
# KAR HEDEFİ YOK! SMA5'i yukarı kırınca satacağız.
TEST_SURESI_YIL = 1       # Son 1 yıl (Güncel piyasa refleksi)
KOMISYON = 1.5            
VERGI_ORANI = 0.15        

# --- PİRANHA SKORLAMA (Mean Reversion) ---
def sinyal_kontrol(row):
    try:
        # İndikatörleri al
        close = float(row['Close'])
        rsi2 = float(row['RSI_2'])       # Çok hızlı RSI
        sma200 = float(row['SMA_200'])   # Ana Trend
    except: return None

    # KURAL 1: Ana Trend Yukarı Olsun (İsteğe bağlı, kaldırırsan daha çok işlem çıkar ama risk artar)
    if close < sma200: return "YOK"

    # KURAL 2: ALIM SİNYALİ (Korkuyu Satın Al)
    # RSI(2) < 10 ise piyasa paniktedir. Burası alım yeridir.
    if rsi2 < 10:
        return "AL"
    
    return "YOK"

def main():
    print("\n" + "="*60)
    print(f"🐟 SAZLIK v8.0 - PİRANHA MODU (Larry Connors RSI 2)")
    print(f"🎯 Hedef: Vur-Kaç (SMA 5 Dönüşü)")
    print(f"💰 Kasa: ${BASLANGIC_KASA} | 🍰 Dilim: %{ISLEM_BASI_YUZDE*100}")
    print("="*60)

    # 1. VERİLERİ HAZIRLA
    print("⏳ Volatil hisseler taranıyor...")
    market_data = {}
    tum_tarihler = set()

    for t in TEST_TICKERS:
        try:
            df = yf.download(t, period=f"{TEST_SURESI_YIL}y", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if len(df) > 100:
                # ÖZEL İNDİKATÖRLER
                df.ta.rsi(length=2, append=True) # RSI 2 (Sır burada)
                df.ta.sma(length=5, append=True) # Çıkış için SMA 5
                df.ta.sma(length=200, append=True) # Trend filtresi
                
                market_data[t] = df
                tum_tarihler.update(df.index)
        except: continue

    if not market_data: 
        print("❌ Veri bulunamadı.")
        return

    zaman_cizelgesi = sorted(list(tum_tarihler))
    
    # 2. SİMÜLASYON
    nakit = BASLANGIC_KASA
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
                portfoy_degeri += poz['adet'] * poz['maliyet']

        # B. SATIŞ (SMA 5 ÇIKIŞI)
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            curr = row['Close']
            sma5 = row['SMA_5']
            
            sebeb = ""
            cikis_fiyati = 0
            
            # PİRANHA ÇIKIŞ KURALI:
            # Fiyat 5 günlük ortalamanın üzerine çıktığı an sat! (Ortalamaya döndü)
            if curr > sma5:
                cikis_fiyati = curr
                sebeb = "SMA5 DÖNÜŞÜ (KAR)"
            
            # Acil Durum Stopu (Çok derin düşüşlerde kol kesmek için)
            elif curr <= poz['maliyet'] * (1 - STOP_LOSS):
                cikis_fiyati = poz['maliyet'] * (1 - STOP_LOSS)
                sebeb = "STOP LOSS"

            if sebeb:
                satis_tutari = poz['adet'] * cikis_fiyati
                brut = satis_tutari - (poz['adet'] * poz['maliyet'])
                
                vergi = brut * VERGI_ORANI if brut > 0 else 0
                net = brut - KOMISYON - vergi
                nakit += satis_tutari - KOMISYON - vergi
                toplam_komisyon += KOMISYON
                
                # Gün sayısını hesapla
                try:
                    tarih_fark = (gun - poz['tarih']).days
                except: tarih_fark = 0

                islem_gecmisi.append({
                    'Hisse': t,
                    'Tarih': gun.date(),
                    'Net Kar': round(net, 2),
                    'Yüzde': round((net / (poz['adet'] * poz['maliyet'])) * 100, 2),
                    'Süre': tarih_fark,
                    'Sebep': sebeb
                })
                satilacaklar.append(t)
        
        for t in satilacaklar: del portfoy[t]
            
        # C. ALIŞ (RSI 2 DİP AVCI)
        for t in TEST_TICKERS:
            if t in portfoy: continue 
            if t not in market_data: continue
            if gun not in market_data[t].index: continue
            
            # Kasa kontrolü (En az işlem açacak kadar para var mı?)
            hedef_tutar = portfoy_degeri * ISLEM_BASI_YUZDE
            if nakit < (hedef_tutar + KOMISYON): continue
            
            row = market_data[t].loc[gun]
            sinyal = sinyal_kontrol(row)
            
            if sinyal == "AL":
                fiyat = row['Close']
                adet = hedef_tutar / fiyat
                nakit -= (adet * fiyat + KOMISYON)
                toplam_komisyon += KOMISYON
                
                portfoy[t] = {'adet': adet, 'maliyet': fiyat, 'tarih': gun}
    
    # --- RAPOR ---
    son_deger = nakit
    for t, poz in portfoy.items():
        if not market_data[t].empty:
            son_deger += poz['adet'] * market_data[t].iloc[-1]['Close']
            
    print("\n" + "-"*30)
    print("📊 PİRANHA SONUÇLARI")
    print("-" * 30)
    print(f"Bitiş          : ${son_deger:.2f}")
    kar_zarar = son_deger - BASLANGIC_KASA
    print(f"Net Kar/Zarar  : ${kar_zarar:.2f} (%{kar_zarar/BASLANGIC_KASA*100:.2f})")
    print(f"💸 Komisyon      : ${toplam_komisyon:.2f}")
    
    if islem_gecmisi:
        df = pd.DataFrame(islem_gecmisi)
        win = len(df[df['Net Kar'] > 0])
        print(f"Başarı Oranı   : %{(win/len(df))*100:.1f}")
        print(f"Toplam İşlem   : {len(df)}")
        print(f"Ort. Süre      : {df['Süre'].mean():.1f} Gün")
        print("\n🏆 SON İŞLEMLER:")
        print(df.sort_values('Tarih', ascending=False).head(5)[['Hisse', 'Tarih', 'Net Kar', 'Yüzde']].to_string(index=False))

    if islem_gecmisi:
        pd.DataFrame(islem_gecmisi).to_csv("backtest_portfoy.csv", index=False)

if __name__ == "__main__":
    main()