import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import numpy as np
from datetime import datetime
import warnings

# Gereksiz uyarıları sustur
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- DEVASA WATCHLIST (İsteğin Üzerine Tam Liste) ---
TEST_TICKERS = [
    # --- TEKNOLOJİ & İLETİŞİM ---
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE", 
    "CRM", "CMCSA", "QCOM", "TXN", "AMGN", "INTC", "CSCO", "VZ", "T", "TMUS",
    "NFLX", "ORCL", "MU", "IBM", "PYPL", "INTU", "AMD", "FTNT", "ADI", "NOW",
    "LRCX", "MRVL", "CDNS", "SNPS", "DXCM", "KLAC", "ROST", "ANSS", "MSCI", "CHTR",
    
    # --- FİNANS ---
    "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPY", "BLK", "SCHW",
    "C", "AXP", "CB", "MMC", "AON", "CME", "ICE", "PGR", "ALL", "MET",
    "AIG", "PNC", "USB", "BK", "COF", "DFS", "TRV", "MCO", "CBOE", "RJF",
    "GPN", "FIS", "ZION", "FITB", "STT", "NDAQ", "RF", "KEY", "CFG", "HBAN",
    
    # --- SAĞLIK ---
    "JNJ", "LLY", "UNH", "ABBV", "MRK", "PFE", "DHR", "TMO", "MDT", "SYK",
    "GILD", "BIIB", "VRTX", "BMY", "ISRG", "ABT", "ZTS", "BDX", "BSX",
    "CI", "CVS", "HUM", "HCA", "ELV", "LH", "COO", "ALGN", "HOLX", "DVA",
    "WAT", "RGEN", "IQV", "REGN", "EW", "TECH", "RVTY", "DGX", "INCY", "CRL",
    
    # --- TÜKETİM ---
    "PG", "KO", "PEP", "WMT", "COST", "HD", "MCD", "NKE", "LOW", "TGT",
    "SBUX", "MDLZ", "CL", "PM", "MO", "KR", "DG", "EL", "KHC",
    "GIS", "K", "SYY", "APO", "DECK", "BBY", "WHR", "NWSA", "FOXA", "HAS",
    "MAT", "HOG", "GT", "TPR", "TTC", "VFC", "HBI", "KSS", "ULTA",
    
    # --- ENERJİ & SANAYİ ---
    "XOM", "CVX", "BRK.B", "LMT", "RTX", "BA", "HON", "MMM", "GE", "GD",
    "CAT", "DE", "EOG", "OXY", "SLB", "COP", "PSX", "MPC", "WMB", "KMI",
    "ETN", "AOS", "EMR", "PCAR", "ROK", "SWK", "TDY", "RSG", "WM", "CARR",
    "ITW", "GWW", "WAB", "AAL", "DAL", "UAL", "LUV", "ALK",
    
    # --- DİĞER ---
    "DUK", "NEE", "SO", "EXC", "AEP", "SRE", "WEC", "D", "ED", "XEL",
    "VNQ", "SPG", "PLD", "EQIX", "AMT", "CCI", "HST", "O", "ARE", "PSA",
    "WY", "BXP", "REG", "VTR", "AVB", "ESR", "EPR", "KIM", "FRT",
    "LUMN", "PARA", "FOX", "WBD", "ETSY", "EBAY", "EA", "TTWO", "ZG",
    
    # --- BÜYÜME & YARI İLETKEN ---
    "ASML", "AMAT", "TSM", "MCHP", "TER", "U", "VEEV", "OKTA", "NET", "CRWD", 
    "DDOG", "ZS", "TEAM", "ADSK", "MSI", "FTV", "WDC", "ZBRA", "SWKS", "QDEL",
    "FSLY", "PLUG", "ENPH", "SEDG", "RUN", "SPWR", "BLDP", "FCEL", "BE", "SOL",
    "LI", "NIO", "XPEV", "RIVN", "LCID", "NKLA", "QS", "GOEV",
    "SQ", "COIN", "HOOD", "UPST", "AFRM", "SOFI", "MQ", "BILL", "TOST", "PAYA",
    "MRNA", "BMRN", "CTAS", "EXEL", "IONS", "XBI", "EDIT", "BEAM", "NTLA", "CRSP",
    "MELI", "ROKU", "PTON", "SPOT", "CHWY", "ZM", "DOCU", "FVRR",
    "PINS", "SNAP", "WIX", "SHOP", "SE", "BABA", "JD", "BIDU", "PDD",
    "ROP", "TT", "FLR", "HUBB", "APH", "ECL", "SHW", "PPG", "FMC",
    "MOS", "CF", "NUE", "STLD", "SAVE", "CAR", "RCL", "CCL", "NCLH", "MGM", "WYNN", "LVS", "PENN", "DKNG", "BYND",
    "RBLX", "UBER", "LYFT", "ABNB", "DOX", "FLT", "PRU", "VLO", "DVN", "APA", "MRO", "HAL",
    "BKR", "FTI", "NOV", "TDW", "PAGP", "ENLC", "PAA", "WES"
]

BASLANGIC_KASA = 1000.0   
ISLEM_BASI_YUZDE = 0.20   # Kasanın %20'si (Daha az ama öz işlem)
TEST_SURESI_YIL = 2       # Son 2 yıl
KOMISYON = 1.5            # 1.5 Giriş + 1.5 Çıkış = 3$
VERGI_ORANI = 0.15        

# --- AKILLI SWING STRATEJİSİ ---
def sinyal_kontrol(row):
    try:
        close = float(row['Close'])
        rsi = float(row['RSI_14'])
        sma20 = float(row['SMA_20'])
        sma50 = float(row['SMA_50'])
        sma200 = float(row['SMA_200'])
    except: return None

    # FİLTRE: Sadece Yükseliş Trendindekiler (SMA 200 Üstü)
    if close < sma200: return "YOK"

    # ALIM SİNYALİ:
    # 1. Momentum: RSI > 50 (Güçlü)
    # 2. Trend Teyidi: Fiyat SMA 20'nin üzerinde (Kısa vade yükseliş)
    # 3. Dip Destek: SMA 50'nin üzerinde (Orta vade yükseliş)
    if rsi > 50 and close > sma20 and close > sma50:
        return "AL"
    
    return "YOK"

def main():
    print("\n" + "="*60)
    print(f"🏛️ SAZLIK v9.0 - AKILLI YATIRIMCI (SWING)")
    print(f"🎯 Hedef: Trendi Yakala ve Bırakma (Az İşlem, Çok Kar)")
    print(f"💰 Kasa: ${BASLANGIC_KASA} | 🍰 Dilim: %{ISLEM_BASI_YUZDE*100}")
    print("="*60)

    # 1. VERİLERİ HAZIRLA
    print(f"⏳ {len(TEST_TICKERS)} Hisse Taranıyor (Bu işlem biraz sürebilir)...")
    market_data = {}
    tum_tarihler = set()

    for t in TEST_TICKERS:
        try:
            # Hatalı/Delist hisseleri atlamak için try-except
            df = yf.download(t, period=f"{TEST_SURESI_YIL}y", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if len(df) > 200:
                # Gerekli İndikatörler
                df.ta.rsi(length=14, append=True)
                df.ta.sma(length=20, append=True)  # Çıkış ve Giriş Tetikçisi
                df.ta.sma(length=50, append=True)  # Orta Vade Destek
                df.ta.sma(length=200, append=True) # Ana Trend
                
                market_data[t] = df
                tum_tarihler.update(df.index)
        except: continue # Hata vereni sessizce geç

    if not market_data: 
        print("❌ Veri bulunamadı.")
        return

    zaman_cizelgesi = sorted(list(tum_tarihler))
    
    # 2. SİMÜLASYON
    nakit = BASLANGIC_KASA
    portfoy = {} 
    islem_gecmisi = []
    toplam_komisyon = 0
    
    # İşlem sıklığını azaltmak için sadece her gün kapanışta karar veriyoruz
    for gun in zaman_cizelgesi:
        
        # A. PORTFÖY DEĞERLEME
        portfoy_degeri = nakit
        for t, poz in portfoy.items():
            if gun in market_data[t].index:
                curr = market_data[t].loc[gun]['Close']
                portfoy_degeri += poz['adet'] * curr
            else:
                portfoy_degeri += poz['adet'] * poz['maliyet']

        # B. SATIŞ KONTROLÜ (TREND BİTTİ Mİ?)
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            curr = row['Close']
            sma20 = row['SMA_20']
            
            sebeb = ""
            cikis_fiyati = 0
            
            # ÇIKIŞ STRATEJİSİ:
            # Fiyat 20 günlük ortalamanın altına düştüyse trend zayıflamıştır. SAT.
            # Stop Loss veya Kar Al YOK. Trend ne zaman biterse o zaman satarız.
            if curr < sma20:
                cikis_fiyati = curr
                sebeb = "TREND KIRILIMI (SMA 20 Altı)"
            
            if sebeb:
                satis_tutari = poz['adet'] * cikis_fiyati
                brut = satis_tutari - (poz['adet'] * poz['maliyet'])
                
                vergi = brut * VERGI_ORANI if brut > 0 else 0
                net = brut - KOMISYON - vergi
                nakit += satis_tutari - KOMISYON - vergi
                toplam_komisyon += KOMISYON
                
                tarih_fark = (gun - poz['tarih']).days

                islem_gecmisi.append({
                    'Hisse': t,
                    'Tarih': gun.date(),
                    'Net Kar': round(net, 2),
                    'Yüzde': round((net / (poz['adet'] * poz['maliyet'])) * 100, 2),
                    'Süre (Gün)': tarih_fark,
                    'Sebep': sebeb
                })
                satilacaklar.append(t)
        
        for t in satilacaklar: del portfoy[t]
            
        # C. YENİ ALIŞ (TREND BAŞLADI MI?)
        # Eğer elimizde nakit varsa ve portföy dolu değilse
        if nakit > 50: 
            potansiyel_adaylar = []
            for t in TEST_TICKERS:
                if t in portfoy: continue 
                if t not in market_data: continue
                if gun not in market_data[t].index: continue
                
                row = market_data[t].loc[gun]
                if sinyal_kontrol(row) == "AL":
                    potansiyel_adaylar.append(t)
            
            # Rastgele değil, RSI gücüne göre en iyileri seçelim
            # (Basitlik için listedeki ilk uygunları alacağız)
            for t in potansiyel_adaylar:
                hedef_tutar = portfoy_degeri * ISLEM_BASI_YUZDE
                if nakit < (hedef_tutar + KOMISYON): break # Para bitti
                
                row = market_data[t].loc[gun]
                fiyat = row['Close']
                adet = hedef_tutar / fiyat
                
                nakit -= (adet * fiyat + KOMISYON)
                toplam_komisyon += KOMISYON
                
                portfoy[t] = {'adet': adet, 'maliyet': fiyat, 'tarih': gun}
    
    # --- SONUÇ RAPORU ---
    son_deger = nakit
    for t, poz in portfoy.items():
        if not market_data[t].empty:
            son_deger += poz['adet'] * market_data[t].iloc[-1]['Close']
            
    print("\n" + "-"*30)
    print("📊 AKILLI YATIRIMCI SONUÇLARI")
    print("-" * 30)
    print(f"Başlangıç      : ${BASLANGIC_KASA:.2f}")
    print(f"Bitiş          : ${son_deger:.2f}")
    kar_zarar = son_deger - BASLANGIC_KASA
    print(f"Net Kar/Zarar  : ${kar_zarar:.2f} (%{kar_zarar/BASLANGIC_KASA*100:.2f})")
    print(f"💸 Komisyon      : ${toplam_komisyon:.2f}")
    
    if islem_gecmisi:
        df = pd.DataFrame(islem_gecmisi)
        win = len(df[df['Net Kar'] > 0])
        print(f"Başarı Oranı   : %{(win/len(df))*100:.1f}")
        print(f"Toplam İşlem   : {len(df)}")
        print(f"Ort. Süre      : {df['Süre (Gün)'].mean():.1f} Gün")
        print("\n🏆 EN YÜKSEK KARLI İŞLEMLER:")
        print(df.sort_values('Net Kar', ascending=False).head(5)[['Hisse', 'Tarih', 'Net Kar', 'Yüzde', 'Süre (Gün)']].to_string(index=False))

    if islem_gecmisi:
        pd.DataFrame(islem_gecmisi).to_csv("backtest_portfoy.csv", index=False)

if __name__ == "__main__":
    main()