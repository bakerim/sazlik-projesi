import streamlit as st

# --- API ANAHTAR YÖNETİMİ ---
# Streamlit Cloud'da 'Secrets' kullanır, lokalde boş geçer (Hata vermemesi için)
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except:
    # Bilgisayarında test ederken buraya manuel yazabilirsin veya boş bırakabilirsin
    GEMINI_API_KEY = "MANUEL_KEY_GIRILEBILIR"
    GITHUB_TOKEN = ""

# --- İZLEME LİSTESİ (Watchlist) ---
# Teknoloji, Sanayi ve Savunma Karması (WDC Eklendi)
WATCHLIST_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE", 
    "CRM", "CMCSA", "QCOM", "TXN", "AMGN", "INTC", "CSCO", "VZ", "T", "TMUS",
    "NFLX", "ORCL", "MU", "IBM", "PYPL", "INTU", "AMD", "FTNT", "ADI", "NOW",
    "LRCX", "MRVL", "CDNS", "SNPS", "DXCM", "KLAC", "ROST", "MSCI", "CHTR",
    "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPY", "BLK", "SCHW",
    "C", "AXP", "CB", "MMC", "AON", "CME", "ICE", "PGR", "ALL", "MET",
    "AIG", "PNC", "USB", "BK", "COF", "TRV", "MCO", "CBOE", "RJF",
    "GPN", "FIS", "ZION", "FITB", "STT", "NDAQ", "RF", "KEY", "CFG", "HBAN",
    "JNJ", "LLY", "UNH", "ABBV", "MRK", "PFE", "DHR", "TMO", "MDT", "SYK",
    "GILD", "BIIB", "VRTX", "BMY", "ISRG", "ABT", "ZTS", "BDX", "BSX",
    "CI", "CVS", "HUM", "HCA", "LH", "COO", "ALGN", "HOLX", "DVA",
    "WAT", "RGEN", "IQV", "REGN", "EW", "TECH", "DGX", "INCY", "CRL",
    "PG", "KO", "PEP", "WMT", "COST", "HD", "MCD", "NKE", "LOW", "TGT",
    "SBUX", "MDLZ", "CL", "PM", "MO", "KR", "DG", "EL", "KHC",
    "GIS", "K", "SYY", "APO", "DECK", "BBY", "WHR", "NWSA", "FOXA", "HAS",
    "MAT", "HOG", "GT", "TPR", "TTC", "VFC", "HBI", "KSS", "ULTA",
    "XOM", "CVX", "LMT", "RTX", "BA", "HON", "MMM", "GE", "GD",
    "CAT", "DE", "EOG", "OXY", "COP", "PSX", "MPC", "WMB", "KMI",
    "ETN", "AOS", "EMR", "PCAR", "ROK", "SWK", "TDY", "RSG", "WM", "CARR",
    "ITW", "GWW", "WAB", "IEX", "AAL", "DAL", "UAL", "LUV", "ALK",
    "DUK", "NEE", "SO", "EXC", "AEP", "SRE", "WEC", "D", "ED", "XEL",
    "VNQ", "SPG", "PLD", "EQIX", "AMT", "CCI", "HST", "O", "ARE", "PSA",
    "WY", "BXP", "REG", "VTR", "AVB", "KIM", "FRT",
    "LUMN", "FOX", "EBAY", "EA", "TTWO", "ZG", "ASML", "AMAT", "TSM", "MCHP", 
    "TER", "U", "VEEV", "OKTA", "NET", "CRWD", "DDOG", "ZS", "TEAM", "ADSK", 
    "MSI", "FTV", "WDC", "ZBRA", "SWKS", "QDEL", "FSLY", "PLUG", "SEDG", 
    "RUN", "SPWR", "BLDP", "FCEL", "BE", "SOL", "LI", "NIO", "XPEV", "RIVN", 
    "LCID", "QS", "GOEV", "COIN", "HOOD", "UPST", "AFRM", "SOFI", "MQ", "BILL", 
    "TOST", "BRZE", "DOCU", "SABR", "TTEC", "TWLO", "RNG", "ZM", "MRNA", 
    "BMRN", "CTAS", "CORT", "EXEL", "IONS", "XBI", "LABU", "EDIT", "BEAM", 
    "NTLA", "CRSP", "MELI", "ROKU", "PTON", "SPOT", "CHWY", "FVRR", "PINS", 
    "WIX", "SHOP", "SE", "BABA", "JD", "BIDU", "PDD", "ROP", "TT", "FLR", 
    "HUBB", "APH", "ECL", "SHW", "PPG", "FMC", "MOS", "CF", "NUE", "STLD", 
    "RCL", "NCLH", "MGM", "WYNN", "LVS", "PENN", "DKNG", "BYND",
    "RBLX", "UBER", "LYFT", "ABNB", "DOX", "PRU", "L", "VLO", "DVN", "APA", 
    "HAL", "BKR", "FTI", "NOV", "TDW", "PAGP", "PAA", "WES"
]