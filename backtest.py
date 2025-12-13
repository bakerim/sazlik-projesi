import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import numpy as np
from datetime import datetime

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

BASLANGIC_KASA = 1000.0   # 1000$
ISLEM_BASI_YUZDE = 0.05   # %5 (Her işleme kasanın %5'i)
STOP_LOSS = 0.05          # %5 Zarar Kes
TAKE_PROFIT = 0.15        # %15 Kar Al
TEST_SURESI_YIL = 2       
KOMISYON = 1.5            # Tek yön (Giriş 1.5, Çıkış 1.5)
VERGI_ORANI = 0.15        # %15 (Sadece kardan)

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

    # Trend Filtresi (Ayı piyasasında alma)
    if close < sma200: return 0 

    if rsi < 30: score += 30      
    elif rsi < 45: score += 15    
    elif rsi > 70: score -= 50    
    
    if sma50 > sma200: score += 10
    if close > sma50: score += 10
    
    return score

def main():
    print("\n" + "="*60)
    print(f"🛡️  GARANTİCİ BABA - PORTFÖY SİMÜLASYONU")
    print(f"💰 Başlangıç: ${BASLANGIC_KASA} | 🍰 İşlem Boyutu: %{ISLEM_BASI_YUZDE*100}")
    print(f"💸 Komisyon: ${KOMISYON*2} (Toplam) | 🏛️ Vergi: %{VERGI_ORANI*100}")
    print("="*60)

    # 1. VERİLERİ HAZIRLA
    print("⏳ Veriler indiriliyor ve işleniyor...")
    market_data = {}
    tum_tarihler = set()

    for t in TEST_TICKERS:
        try:
            df = yf.download(t, period=f"{TEST_SURESI_YIL}y", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if len(df) > 200:
                df.ta.rsi(length=14, append=True)
                df.ta.sma(length=50, append=True)
                df.ta.sma(length=200, append=True)
                market_data[t] = df
                tum_tarihler.update(df.index)
        except: continue

    # Tarihleri sırala (Zaman çizelgesi)
    zaman_cizelgesi = sorted(list(tum_tarihler))
    
    # 2. SİMÜLASYON DEĞİŞKENLERİ
    nakit = BASLANGIC_KASA
    portfoy = {} # { 'AAPL': {'adet': 5, 'maliyet': 150, 'tarih': ...} }
    
    islem_gecmisi = []
    toplam_komisyon = 0
    toplam_vergi = 0
    
    # Zaman yolculuğu başlıyor
    for gun in zaman_cizelgesi:
        # A. PORTFÖY DEĞERİNİ HESAPLA (Nakit + Açık Pozisyonlar)
        portfoy_degeri = nakit
        for t, poz in portfoy.items():
            if gun in market_data[t].index:
                guncel_fiyat = market_data[t].loc[gun]['Close']
                portfoy_degeri += poz['adet'] * guncel_fiyat
            else:
                # Veri yoksa maliyetten say (Haftasonu vs.)
                portfoy_degeri += poz['adet'] * poz['maliyet']

        # B. POZİSYONLARI KONTROL ET (Çıkış Var mı?)
        satilacaklar = []
        for t, poz in portfoy.items():
            if gun not in market_data[t].index: continue
            
            row = market_data[t].loc[gun]
            fiyat = row['Close']
            yuksek = row['High']
            dusuk = row['Low']
            
            # Puanı anlık hesapla
            puan = skor_hesapla(row)
            
            sebeb = ""
            cikis_fiyati = 0
            
            # Stop Loss
            if dusuk <= poz['maliyet'] * (1 - STOP_LOSS):
                cikis_fiyati = poz['maliyet'] * (1 - STOP_LOSS)
                sebeb = "STOP"
            # Kar Al
            elif yuksek >= poz['maliyet'] * (1 + TAKE_PROFIT):
                cikis_fiyati = poz['maliyet'] * (1 + TAKE_PROFIT)
                sebeb = "KAR AL"
            # Teknik Bozulma
            elif puan <= 40:
                cikis_fiyati = fiyat
                sebeb = "TEKNİK SATIŞ"
            
            if sebeb:
                # SATIŞ İŞLEMİ
                satis_tutari = poz['adet'] * cikis_fiyati
                brut_kar = satis_tutari - (poz['adet'] * poz['maliyet'])
                
                # Masraflar
                komisyon = KOMISYON # Çıkış komisyonu
                vergi = 0
                if brut_kar > 0:
                    vergi = brut_kar * VERGI_ORANI
                
                net_kar = brut_kar - komisyon - vergi
                
                # Nakite ekle
                nakit += satis_tutari - komisyon - vergi
                
                # İstatistikleri güncelle
                toplam_komisyon += komisyon
                toplam_vergi += vergi
                
                islem_gecmisi.append({
                    'Hisse': t,
                    'Tarih': gun.date(),
                    'İşlem': 'SATIŞ',
                    'Fiyat': round(cikis_fiyati, 2),
                    'Net Kar': round(net_kar, 2),
                    'Yüzde': round((net_kar / (poz['adet'] * poz['maliyet'])) * 100, 2),
                    'Sebep': sebeb
                })
                satilacaklar.append(t)
        
        # Satılanları portföyden düş
        for t in satilacaklar:
            del portfoy[t]
            
        # C. YENİ FIRSATLARI TARA (Giriş Var mı?)
        # 200. günden sonra başla (SMA200 oluşması için)
        # Basit bir kontrol: Günün indeksi > 200 olmalı ama burada tarih bazlı gidiyoruz.
        # Basit çözüm: Eğer hissenin verisi o gün mevcutsa ve yeterli geçmiş varsa.
        
        for t in TEST_TICKERS:
            if t in portfoy: continue # Zaten elimizde var
            if t not in market_data: continue
            if gun not in market_data[t].index: continue
            
            # Yeterli nakit var mı? (Komisyonu da düşünerek)
            # Hedef işlem büyüklüğü: Güncel Portföy Değerinin %5'i
            hedef_islem_tutari = portfoy_degeri * ISLEM_BASI_YUZDE
            
            # Eğer hedef tutar 20$'ın altındaysa işlem açma (Komisyon %10'u geçer, mantıksız)
            if hedef_islem_tutari < 20: continue
            if nakit < (hedef_islem_tutari + KOMISYON): continue
            
            row = market_data[t].loc[gun]
            puan = skor_hesapla(row)
            
            # ALIM EŞİĞİ (SNIPER)
            if puan >= 75:
                fiyat = row['Close']
                # Adet hesabı (Parçalı hisse alabiliyoruz)
                adet = hedef_islem_tutari / fiyat
                
                # ALIM İŞLEMİ
                maliyet_tutari = adet * fiyat
                nakit -= (maliyet_tutari + KOMISYON)
                toplam_komisyon += KOMISYON
                
                portfoy[t] = {
                    'adet': adet,
                    'maliyet': fiyat,
                    'tarih': gun
                }
                
                # Giriş kaydı tutmaya gerek yok, sadece çıkışları raporluyoruz
    
    # --- RAPORLAMA ---
    print("\n" + "-"*30)
    print("📊 PORTFÖY SONUÇ RAPORU")
    print("-"*30)
    
    son_deger = nakit
    # Kalan hisseleri nakite çevirmeden değerini ekle
    for t, poz in portfoy.items():
        if not market_data[t].empty:
            son_fiyat = market_data[t].iloc[-1]['Close']
            son_deger += poz['adet'] * son_fiyat
            
    kar_zarar = son_deger - BASLANGIC_KASA
    yuzde_degisim = (kar_zarar / BASLANGIC_KASA) * 100
    
    print(f"Başlangıç Kasası : ${BASLANGIC_KASA:.2f}")
    print(f"Bitiş Kasası     : ${son_deger:.2f}")
    print(f"Net Kar/Zarar    : ${kar_zarar:.2f} (%{yuzde_degisim:.2f})")
    print("-" * 30)
    print(f"💸 Ödenen Komisyon: ${toplam_komisyon:.2f}")
    print(f"🏛️ Ödenen Vergi   : ${toplam_vergi:.2f}")
    print(f"Toplam İşlem     : {len(islem_gecmisi)}")
    
    if islem_gecmisi:
        df_res = pd.DataFrame(islem_gecmisi)
        win = len(df_res[df_res['Net Kar'] > 0])
        print(f"Başarı Oranı     : %{(win/len(df_res))*100:.1f}")
        
        print("\n🏆 EN İYİ İŞLEMLER:")
        print(df_res.sort_values('Net Kar', ascending=False).head(3)[['Hisse', 'Tarih', 'Net Kar', 'Yüzde']].to_string(index=False))

    # CSV Kayıt
    if islem_gecmisi:
        pd.DataFrame(islem_gecmisi).to_csv("backtest_portfoy.csv", index=False)
        print("\n💾 Detaylar 'backtest_portfoy.csv' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()