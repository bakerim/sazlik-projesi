import yfinance as yf
import pandas as pd
import time
import random
import os

# --- 🔥 SAZLIK 500: DEV LİSTE ---
WATCHLIST = [
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

# Tekrarları temizle
WATCHLIST = list(set(WATCHLIST))

def calculate_rsi(series, period=14):
    """Göreceli Güç Endeksi (RSI) Hesaplar"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_financial_data(ticker_symbol):
    """Hem TEMEL hem de TEKNİK verileri çeker."""
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # --- TEKNİK (Hızlı) ---
        hist = stock.history(period="1y")
        if hist.empty: return None
        
        current_price = hist['Close'].iloc[-1]
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        rsi_val = calculate_rsi(hist['Close']).iloc[-1]
        
        tech_score = 0
        trend_status = "Nötr"
        if current_price > sma_200: 
            tech_score += 20
            trend_status = "Yükseliş"
        if current_price > sma_50: tech_score += 10
        if 30 < rsi_val < 70: tech_score += 10
        elif rsi_val < 30: tech_score += 15

        # --- TEMEL (Yavaş) ---
        info = stock.info
        pe_ratio = info.get('forwardPE', 0)
        debt_equity = info.get('debtToEquity', 0)
        profit_margins = info.get('profitMargins', 0)
        
        fund_score = 0
        if pe_ratio and 0 < pe_ratio < 25: fund_score += 20
        if debt_equity and debt_equity < 150: fund_score += 15
        if profit_margins and profit_margins > 0.10: fund_score += 15

        total_score = tech_score + fund_score
        
        return {
            "Sembol": ticker_symbol,
            "Fiyat": round(current_price, 2),
            "Sazlık_Skoru": total_score,
            "Trend": trend_status,
            "RSI": round(rsi_val, 2),
            "F/K": round(pe_ratio, 2) if pe_ratio else 0,
            "Karar": "GÜÇLÜ ADAY" if total_score > 70 else "İZLE"
        }

    except Exception as e:
        # print(f"⚠️ Hata ({ticker_symbol}): {e}") # Konsolu kirletmemesi için kapattım
        return None

def main_analysis():
    print(f"🚀 Sazlık Motoru Çalışıyor... ({len(WATCHLIST)} Hisse)")
    print("💾 Veriler her 5 hissede bir 'sazlik_analiz_sonuclari.csv' dosyasına kaydedilecek.\n")
    
    # Eğer önceden dosya varsa, üzerine yazmasın diye kontrol edilebilir ama
    # şimdilik sıfırdan başlatalım.
    results = []
    processed_count = 0
    
    for ticker in WATCHLIST:
        print(f"⚙️ {ticker}...", end=" ", flush=True)
        
        data = get_financial_data(ticker)
        
        if data:
            results.append(data)
            print(f"✅ ({data['Sazlık_Skoru']})", end=" ")
        else:
            print("❌", end=" ")
            
        processed_count += 1
        
        # --- CANLI KAYIT SİSTEMİ (HER 5 HİSSEDE BİR) ---
        if processed_count % 5 == 0:
            df = pd.DataFrame(results)
            df.to_csv("sazlik_analiz_sonuclari.csv", index=False)
            print(f"💾 [KAYDEDİLDİ]")
        
        # Hız Sınırı (Ban Yememek İçin)
        time.sleep(random.uniform(1.5, 3.5))
    
    # Döngü bitince son kez kaydet
    if results:
        df = pd.DataFrame(results)
        df.to_csv("sazlik_analiz_sonuclari.csv", index=False)
        print("\n🏁 TÜM ANALİZ TAMAMLANDI.")

if __name__ == "__main__":
    main_analysis()