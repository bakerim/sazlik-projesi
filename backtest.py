import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import numpy as np
from datetime import datetime
import warnings

# Gereksiz uyarıları sustur
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- AYARLAR ---
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
ISLEM_BASI_YUZDE = 0.25   # DİKKAT: %5 yerine %25 ile giriyoruz! (Daha büyük oyun)
STOP_LOSS = 0.10          # %5 yerine %10 (Daha geniş alan)
TAKE_PROFIT = 0.20        # %15 yerine %20
TEST_SURESI_YIL = 2       
KOMISYON = 1.5            # 1.5 Giriş + 1.5 Çıkış
VERGI_ORANI = 0.15        

# --- SNIPER SKORLAMA ---
def skor_hesapla(row):
    score = 50
    try:
        rsi = float(row['RSI_14'])
        close = float(row['Close'])
        sma50 = float(row['SMA_50'])
        sma200 = float(row['SMA_200'])
    except: return 0
    
    if pd.isna(rsi) or pd.isna(sma200): return 0

    # Trend Filtresi: 200 günlüğün altındaysa ASLA ALMA
    if close < sma200: return 0 

    # RSI çok düşükse al (Dipten toplama stratejisi)
    if rsi < 30: score += 40      
    elif rsi < 45: score += 20    
    elif rsi > 70: score -= 50    
    
    # Golden Cross desteği
    if sma50 > sma200: score += 10
    
    return score

def main():
    print("\n" + "="*60)
    print(f"🐋  GARANTİCİ BABA - BALİNA MODU (Yüksek Risk/Yüksek Getiri)")
    print(f"💰 Başlangıç: ${BASLANGIC_KASA} | 🍰 İşlem Boyutu: %{ISLEM_BASI_YUZDE*100}")
    print(f"🛑 Stop: %{STOP_LOSS*100} | 🎯 Hedef: %{TAKE_PROFIT*100}")
    print("="*60)

    # 1. VERİLERİ HAZIRLA
    print("⏳ Veriler indiriliyor...")
    market_data = {}
    tum_tarihler = set()

    for t in TEST_TICKERS:
        try:
            df = yf.download(t, period=f"{TEST_SURESI_YIL}y", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if len(df) > 200:
                df.ta.rsi(length=14, append=True)
                df.ta.sma(length=50, append=True)
                df.ta.sma(length=200, append=True)
                market_data[t] = df
                tum_tarihler.update(df.index)
        except: continue

    if not market_data:
        print("❌ Veri çekilemedi.")
        return

    zaman_cizelgesi = sorted(list(tum_tarihler))
    
    # 2. SİMÜLASYON
    nakit = BASLANGIC_KASA
    portfoy = {} 
    islem_gecmisi = []
    toplam_komisyon = 0
    toplam_vergi = 0
    
    for gun in zaman_cizelgesi:
        # A. PORTFÖY GÜNCELLEME
        portfoy_degeri = nakit
        for t, poz in portfoy.items():
            if gun in market_data[t].index:
                guncel_fiyat = market_data[t].loc[gun]['Close']
                portfoy_degeri += poz['adet'] * guncel_fiyat
            else:
                portfoy_degeri += poz['adet'] * poz['maliyet']

        # B. SATIŞ KONTROLÜ
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            fiyat = row['Close']
            yuksek = row['High']
            dusuk = row['Low']
            puan = skor_hesapla(row)
            
            sebeb = ""
            cikis_fiyati = 0
            
            if dusuk <= poz['maliyet'] * (1 - STOP_LOSS):
                cikis_fiyati = poz['maliyet'] * (1 - STOP_LOSS)
                sebeb = "STOP"
            elif yuksek >= poz['maliyet'] * (1 + TAKE_PROFIT):
                cikis_fiyati = poz['maliyet'] * (1 + TAKE_PROFIT)
                sebeb = "KAR AL"
            elif puan <= 35: # Teknik çıkışı da gevşettik
                cikis_fiyati = fiyat
                sebeb = "TEKNİK SATIŞ"
            
            if sebeb:
                satis_tutari = poz['adet'] * cikis_fiyati
                brut_kar = satis_tutari - (poz['adet'] * poz['maliyet'])
                
                komisyon = KOMISYON 
                vergi = 0
                if brut_kar > 0:
                    vergi = brut_kar * VERGI_ORANI
                
                net_kar = brut_kar - komisyon - vergi
                nakit += satis_tutari - komisyon - vergi
                
                toplam_komisyon += komisyon
                toplam_vergi += vergi
                
                islem_gecmisi.append({
                    'Hisse': t,
                    'Tarih': gun.date(),
                    'İşlem': 'SATIŞ',
                    'Net Kar': round(net_kar, 2),
                    'Yüzde': round((net_kar / (poz['adet'] * poz['maliyet'])) * 100, 2),
                    'Sebep': sebeb
                })
                satilacaklar.append(t)
        
        for t in satilacaklar:
            del portfoy[t]
            
        # C. ALIŞ KONTROLÜ
        for t in TEST_TICKERS:
            if t in portfoy: continue 
            if t not in market_data: continue
            if gun not in market_data[t].index: continue
            
            # Kasanın %25'i ile giriyoruz!
            hedef_islem_tutari = portfoy_degeri * ISLEM_BASI_YUZDE
            
            if nakit < (hedef_islem_tutari + KOMISYON): continue
            
            row = market_data[t].loc[gun]
            puan = skor_hesapla(row)
            
            # Sadece 70 ve üzeri (Kaliteli Giriş)
            if puan >= 70:
                fiyat = row['Close']
                adet = hedef_islem_tutari / fiyat
                
                nakit -= (adet * fiyat + KOMISYON)
                toplam_komisyon += KOMISYON
                
                portfoy[t] = {
                    'adet': adet,
                    'maliyet': fiyat,
                    'tarih': gun
                }
    
    # --- SONUÇ ---
    print("\n" + "-"*30)
    print("📊 BALİNA MODU SONUÇLARI")
    print("-"*30)
    
    son_deger = nakit
    for t, poz in portfoy.items():
        if not market_data[t].empty:
            son_fiyat = market_data[t].iloc[-1]['Close']
            son_deger += poz['adet'] * son_fiyat
            
    kar_zarar = son_deger - BASLANGIC_KASA
    yuzde_degisim = (kar_zarar / BASLANGIC_KASA) * 100
    
    print(f"Başlangıç      : ${BASLANGIC_KASA:.2f}")
    print(f"Bitiş          : ${son_deger:.2f}")
    print(f"Net Kar/Zarar  : ${kar_zarar:.2f} (%{yuzde_degisim:.2f})")
    print("-" * 30)
    print(f"💸 Komisyon      : ${toplam_komisyon:.2f}")
    print(f"Toplam İşlem   : {len(islem_gecmisi)}")
    
    if islem_gecmisi:
        df_res = pd.DataFrame(islem_gecmisi)
        win = len(df_res[df_res['Net Kar'] > 0])
        print(f"Başarı Oranı   : %{(win/len(df_res))*100:.1f}")
        
        print("\n🏆 EN İYİ İŞLEMLER:")
        print(df_res.sort_values('Net Kar', ascending=False).head(3)[['Hisse', 'Tarih', 'Net Kar', 'Yüzde']].to_string(index=False))

    if islem_gecmisi:
        pd.DataFrame(islem_gecmisi).to_csv("backtest_portfoy.csv", index=False)

if __name__ == "__main__":
    main()