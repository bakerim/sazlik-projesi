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

# Listeyi temizle ve karıştır (Ban yememek için karışık sıra iyidir)
WATCHLIST = list(set(WATCHLIST))
random.shuffle(WATCHLIST) 

def calculate_atr(hist, period=14):
    """Volatiliteyi (ATR) Hesaplar"""
    high_low = hist['High'] - hist['Low']
    high_close = (hist['High'] - hist['Close'].shift()).abs()
    low_close = (hist['Low'] - hist['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

def get_swing_trade_setup(ticker_symbol):
    """
    Hisse için Gerçekçi ve Dinamik R/R Oranına sahip seviyeleri belirler.
    Güncelleme: Hedef çarpanları düşürülerek daha ulaşılabilir hedefler sağlandı.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # Son 6 aylık veriyi çek (Trend analizi için)
        hist = stock.history(period="6mo")
        if hist.empty: return None
        
        # --- TEKNİK VERİLER ---
        current_price = hist['Close'].iloc[-1]
        atr_value = calculate_atr(hist).iloc[-1]
        
        # Hareketli Ortalamalar
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        
        # RSI Hesaplama
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_val = (100 - (100 / (1 + rs))).iloc[-1]

        # --- DİNAMİK STRATEJİ (KONSERVATİF MOD) ---
        
        # 1. STOP LOSS HESABI
        # Volatilite yüksekse stopu biraz daha geniş tut (tuzağa düşmemek için)
        volatility_pct = (atr_value / current_price) * 100
        stop_multiplier = 1.8 if volatility_pct < 2.0 else 2.2
        stop_loss = current_price - (stop_multiplier * atr_value)
        
        # 2. HEDEF (TAKE PROFIT) HESABI - GÜNCELLENDİ
        # Baz Çarpan: Eskiden 3.0 idi, şimdi 2.0 (Daha gerçekçi)
        target_multiplier = 2.0 
        
        # RSI ve Trend ile İnce Ayar
        # RSI Düşükse (35 altı) tepki potansiyeli var -> Hedefi hafif artır (+0.5)
        if rsi_val < 35:
            target_multiplier += 0.5
            
        # RSI Yüksekse (70 üstü) düzeltme riski var -> Hedefi kıs (-0.5)
        if rsi_val > 70:
            target_multiplier -= 0.5

        # Trend Çok Güçlüyse (Golden Cross + Fiyat Üstte) -> Momentum bonusu (+1.0)
        if current_price > sma_50 and sma_50 > sma_200:
            target_multiplier += 1.0
            
        # Hedef Fiyat
        target_price = current_price + (target_multiplier * atr_value)
        
        # R/R Hesaplama
        risk = current_price - stop_loss
        reward = target_price - current_price
        
        if risk <= 0: return None
        rr_ratio = reward / risk
        
        # Vade Tahmini (Volatiliteye göre)
        # Volatilite çok yüksekse hareketler hızlı gerçekleşir (Kısa Vade)
        if volatility_pct > 3.5: vade = "Kısa (1-3 Gün)"
        elif volatility_pct > 2.0: vade = "Orta (1-2 Hafta)"
        else: vade = "Uzun (2-5 Hafta)"

        # Trend Yönü
        trend = "Nötr"
        if current_price > sma_50: trend = "Yükseliş"
        elif current_price < sma_50: trend = "Düşüş"

        return {
            "SEMBL": ticker_symbol,
            "GÜNCEL": round(current_price, 2),
            "GİRİŞ": round(current_price, 2), # Anlık Fiyat
            "HEDEF": round(target_price, 2),
            "STOP": round(stop_loss, 2),
            "R/R": round(rr_ratio, 2),
            "VADE": vade,
            "ATR": round(atr_value, 2),
            "TREND": trend
        }

    except Exception as e:
        return None

def main_analysis():
    print(f"🎯 Sazlık Swing Masası Kuruluyor... ({len(WATCHLIST)} Hisse)")
    print("💾 Veriler her 5 hissede bir 'sazlik_swing_data.csv' dosyasına kaydedilecek.\n")
    
    results = []
    processed = 0
    
    for ticker in WATCHLIST:
        print(f"🔭 {ticker}...", end=" ", flush=True)
        
        setup = get_swing_trade_setup(ticker)
        
        if setup:
            results.append(setup)
            print(f"✅ R/R: {setup['R/R']} | {setup['TREND']}")
        else:
            print("❌ Veri Yok/Hata")
            
        processed += 1
        
        # --- CANLI KAYIT (Her 5 hissede bir) ---
        if processed % 5 == 0:
            df = pd.DataFrame(results)
            df.to_csv("sazlik_swing_data.csv", index=False)
            # print("💾 [KAYDEDİLDİ]", end=" ") 
        
        # Hız Sınırı (Yahoo Ban Koruması - Rastgele Bekleme)
        time.sleep(random.uniform(1.2, 3.0))

    # Döngü bitince son kayıt
    if results:
        df = pd.DataFrame(results)
        df.to_csv("sazlik_swing_data.csv", index=False)
        print("\n🏁 Taramalar Tamamlandı. Veriler 'sazlik_swing_data.csv' dosyasında.")

if __name__ == "__main__":
    main_analysis()