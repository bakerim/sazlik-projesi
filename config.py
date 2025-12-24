# --- 2. ANA İZLEME LİSTESİ (WATCHLIST) ---
WATCHLIST = [
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
# --- 3. HABER KELİME EŞLEŞTİRMESİ (BOTUN ARADIĞI KELİMELER) ---
# Bu sözlük, haber metnindeki şirket isimlerini Ticker koduna eşler.
# Sadece en popüler olanları tutuyoruz, geri kalanı Ticker koduyla denenecek.
TRACKED_STOCKS = {
    "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL",
    "amazon": "AMZN", "nvidia": "NVDA", "meta": "META", "facebook": "META",
    "tesla": "TSLA", "broadcom": "AVGO", "adobe": "ADBE", "salesforce": "CRM",
    "qualcomm": "QCOM", "amgen": "AMGN", "intel": "INTC", "cisco": "CSCO",
    "verizon": "VZ", "att": "T", "netflix": "NFLX", "oracle": "ORCL",
    "ibm": "IBM", "paypal": "PYPL", "intuit": "INTU", "amd": "AMD",
    "morgan stanley": "MS", "jpmorgan": "JPM", "visa": "V", "mastercard": "MA",
    "bank of america": "BAC", "pfizer": "PFE", "johnson & johnson": "JNJ",
    "walmart": "WMT", "coca cola": "KO", "pepsi": "PEP", "mcdonalds": "MCD",
    "nike": "NKE", "starbucks": "SBUX", "exxon mobil": "XOM", "chevron": "CVX",
    "berkshire hathaway": "BRK.B", "lockheed martin": "LMT", "raytheon": "RTX",
    "boeing": "BA", "general electric": "GE", "general dynamics": "GD",
    "caterpillar": "CAT", "netflix": "NFLX", "spotify": "SPOT", "uber": "UBER",
    "lyft": "LYFT", "airbnb": "ABNB", "etsy": "ETSY", "roku": "ROKU",
    "coinbase": "COIN", "shopify": "SHOP", "alibaba": "BABA", "jd com": "JD"
}


# --- 4. SİSTEM AYARLARI (GEREKLİ) ---
# Botun ve Dashboard'un ortak kullanacağı değişkenler
WATCHLIST_TICKERS = WATCHLIST # İsmi botun anlayacağı dile çeviriyoruz
OUTPUT_FILE = "sazlik_analiz_sonuclari.csv"

# RSS KAYNAKLARI
RSS_URLS = [
    "https://finance.yahoo.com/news/rssindex",
    "https://finance.yahoo.com/topic/stock-market-news/rss",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories"
]
