import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import time
from datetime import datetime

# --- AYARLAR ---
TEST_TICKERS = [
# TEKNOLOJİ DEVLERİ
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE", 
    "CRM", "CMCSA", "QCOM", "TXN", "AMGN", "INTC", "CSCO", "VZ", "T", "TMUS",
    "NFLX", "ORCL", "MU", "IBM", "PYPL", "INTU", "AMD", "FTNT", "ADI", "NOW",
    "LRCX", "MRVL", "CDNS", "SNPS", "DXCM", "KLAC", "ROST", "ANSS", "MSCI", "CHTR",
    
    # FİNANS
    "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPY", "BLK", "SCHW",
    "C", "AXP", "CB", "MMC", "AON", "CME", "ICE", "PGR", "ALL", "MET",
    "AIG", "PNC", "USB", "BK", "COF", "TRV", "MCO", "CBOE", "RJF",
    "GPN", "FIS", "ZION", "FITB", "STT", "NDAQ", "RF", "KEY", "CFG", "HBAN",
    
    # SAĞLIK
    "JNJ", "LLY", "UNH", "ABBV", "MRK", "PFE", "DHR", "TMO", "MDT", "SYK",
    "GILD", "BIIB", "VRTX", "BMY", "ISRG", "ABT", "ZTS", "BDX", "BSX",
    "CI", "CVS", "HUM", "HCA", "ELV", "LH", "COO", "ALGN", "HOLX", "DVA",
    "WAT", "RGEN", "IQV", "REGN", "EW", "TECH", "RVTY", "DGX", "INCY", "CRL",
    
    # TÜKETİM
    "PG", "KO", "PEP", "WMT", "COST", "HD", "MCD", "NKE", "LOW", "TGT",
    "SBUX", "MDLZ", "CL", "PM", "MO", "KR", "DG", "EL", "KHC",
    "GIS", "K", "SYY", "APO", "DECK", "BBY", "WHR", "NWSA", "FOXA", "HAS",
    "MAT", "HOG", "GT", "TPR", "TTC", "VFC", "HBI", "KSS", "ULTA",
    
    # SANAYİ & ENERJİ
    "XOM", "CVX", "BRK.B", "LMT", "RTX", "BA", "HON", "MMM", "GE", "GD",
    "CAT", "DE", "EOG", "OXY", "SLB", "COP", "PSX", "MPC", "WMB", "KMI",
    "ETN", "AOS", "EMR", "PCAR", "ROK", "SWK", "TDY", "RSG", "WM", "CARR",
    "ITW", "GWW", "WAB", "AAL", "DAL", "UAL", "LUV", "ALK",
    
    # DİĞER
    "DUK", "NEE", "SO", "EXC", "AEP", "SRE", "WEC", "D", "ED", "XEL",
    "VNQ", "SPG", "PLD", "EQIX", "AMT", "CCI", "HST", "O", "ARE", "PSA",
    "WY", "BXP", "REG", "VTR", "AVB", "ESR", "EPR", "KIM", "FRT",
    "LUMN", "PARA", "FOX", "WBD", "ETSY", "EBAY", "EA", "TTWO", "ZG",
    
    # YENİ NESİL & BÜYÜME
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

BASLANGIC_BAKIYE = 10000  # Her işleme 10.000$ ile giriyoruz
STOP_LOSS = 0.05          # %5 Zarar Kes
TAKE_PROFIT = 0.15        # %15 Kar Al
TEST_SURESI_YIL = 2       # Son 2 yıl
KOMISYON_ISLEM_BASI = 1.5 # İşlem başı 1.5$ (Alırken 1.5, Satarken 1.5)

def skor_hesapla(row):
    score = 50
    rsi = row['RSI_14']
    close = row['Close']
    sma50 = row['SMA_50']
    sma200 = row['SMA_200']
    
    if pd.isna(rsi) or pd.isna(sma200): return 0

    if rsi < 30: score += 25
    elif rsi < 40: score += 10
    elif rsi > 70: score -= 20
    
    if close > sma200: score += 15
    else: score -= 10
        
    if sma50 > sma200: score += 10
    if close > sma50: score += 5
    return score

def backtest_motoru(ticker):
    print(f"⏳ {ticker} simüle ediliyor...", end=" ")
    
    try:
        df = yf.download(ticker, period=f"{TEST_SURESI_YIL}y", interval="1d", progress=False)
        if len(df) < 200: 
            print("❌ Yetersiz Veri")
            return None, 0
    except:
        print("❌ Veri Hatası")
        return None, 0

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.ta.rsi(length=14, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    
    pozisyon = False
    giris_fiyati = 0
    giris_tarihi = None
    hisse_adedi = 0
    islem_gecmisi = []
    toplam_komisyon_hisse = 0
    
    for i in range(200, len(df)):
        gun = df.index[i]
        row = df.iloc[i]
        fiyat = float(row['Close'])
        yuksek = float(row['High'])
        dusuk = float(row['Low'])
        puan = skor_hesapla(row)
        
        # --- ÇIKIŞ ---
        if pozisyon:
            sebeb = ""
            cikis_fiyati = 0
            
            # Stop veya Kar Al Kontrolü
            if dusuk <= giris_fiyati * (1 - STOP_LOSS):
                cikis_fiyati = giris_fiyati * (1 - STOP_LOSS)
                sebeb = "STOP LOSS"
            elif yuksek >= giris_fiyati * (1 + TAKE_PROFIT):
                cikis_fiyati = giris_fiyati * (1 + TAKE_PROFIT)
                sebeb = "KAR AL"
            elif puan <= 40: 
                cikis_fiyati = fiyat
                sebeb = "TEKNİK BOZULMA"
            
            if sebeb:
                # Hesaplama: (Satış Geliri - Komisyon) - (Alış Maliyeti + Komisyon)
                satis_geliri = (hisse_adedi * cikis_fiyati)
                alis_maliyeti = (hisse_adedi * giris_fiyati)
                
                brut_kar = satis_geliri - alis_maliyeti
                # Toplam 3$ Komisyon (1.5 Giriş + 1.5 Çıkış)
                odenen_komisyon = (KOMISYON_ISLEM_BASI * 2) 
                net_kar = brut_kar - odenen_komisyon
                
                net_yuzde = (net_kar / alis_maliyeti) * 100
                toplam_komisyon_hisse += odenen_komisyon
                
                islem_gecmisi.append({
                    'Hisse': ticker,
                    'Alış': giris_tarihi.date(),
                    'Satış': gun.date(),
                    'Net Kar $': round(net_kar, 2),
                    'Kar %': round(net_yuzde, 2),
                    'Komisyon': odenen_komisyon,
                    'Sebep': sebeb
                })
                pozisyon = False
                continue

        # --- GİRİŞ ---
        if not pozisyon:
            if puan >= 60:
                pozisyon = True
                giris_fiyati = fiyat
                giris_tarihi = gun
                # 10.000$ ile kaç adet alınır?
                hisse_adedi = BASLANGIC_BAKIYE / giris_fiyati
                
                # Giriş Komisyonunu burada kaydetmiyoruz, çıkışta toplu düşüyoruz
                
    print(f"✅ ({len(islem_gecmisi)} İşlem)")
    return islem_gecmisi, toplam_komisyon_hisse

def main():
    print("\n" + "="*60)
    print(f"🛡️  GARANTİCİ BABA - KOMİSYONLU BACKTEST (${KOMISYON_ISLEM_BASI}/işlem)")
    print("="*60)
    
    tum_islemler = []
    toplam_odenen_komisyon = 0
    
    for hisse in TEST_TICKERS:
        islemler, komisyon = backtest_motoru(hisse)
        if islemler:
            tum_islemler.extend(islemler)
            toplam_odenen_komisyon += komisyon
            
    if not tum_islemler:
        print("❌ Hiç işlem yapılmadı.")
        return

    df_res = pd.DataFrame(tum_islemler)
    
    # --- İSTATİSTİKLER ---
    toplam_islem = len(df_res)
    karli = df_res[df_res['Kar %'] > 0]
    zararli = df_res[df_res['Kar %'] <= 0]
    
    win_rate = (len(karli) / toplam_islem) * 100
    avg_return = df_res['Kar %'].mean()
    total_net_profit = df_res['Net Kar $'].sum()
    
    print("\n" + "-"*30)
    print("📊 GENEL PERFORMANS RAPORU")
    print("-"*30)
    print(f"Toplam İşlem     : {toplam_islem}")
    print(f"Başarı Oranı     : %{win_rate:.1f}")
    print(f"Ortalama Getiri  : %{avg_return:.2f} (Net)")
    print(f"Toplam Net Kar   : ${total_net_profit:.2f}")
    print("-" * 30)
    print(f"💸 TOPLAM KOMİSYON : ${toplam_odenen_komisyon:.2f}")
    print("-" * 30)
    
    print("\n🏆 EN İYİ 3 İŞLEM (NET):")
    print(df_res.sort_values('Kar %', ascending=False).head(3)[['Hisse', 'Alış', 'Kar %', 'Net Kar $']].to_string(index=False))
    
    print("\n💀 EN KÖTÜ 3 İŞLEM (NET):")
    print(df_res.sort_values('Kar %', ascending=True).head(3)[['Hisse', 'Alış', 'Kar %', 'Net Kar $']].to_string(index=False))
    
    df_res.to_csv("backtest_sonuc.csv", index=False)
    print("\n💾 Detaylar 'backtest_sonuc.csv' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()
