# Takip Listesi ve İsim Eşleştirmeleri
# Anahtar (Key): Haber metninde aranacak kelime (küçük harfle)
# Değer (Value): Yfinance Ticker Kodu

TRACKED_STOCKS = {
    # Teknoloji Devleri
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",  # GOOGL ve GOOG aynı şirket (Alphabet)
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "nvidia": "NVDA",
    "meta": "META",
    "facebook": "META", # Eski adıyla da yakalasın
    "tesla": "TSLA",
    
    # Çip ve Donanım
    "broadcom": "AVGO",
    "qualcomm": "QCOM",
    "intel": "INTC",
    "amd": "AMD",
    "advanced micro devices": "AMD",
    "micron": "MU",
    "texas instruments": "TXN",
    "analog devices": "ADI",
    "lam research": "LRCX",
    "marvell": "MRVL",
    "kla": "KLAC",
    
    # Yazılım ve Servisler
    "adobe": "ADBE",
    "salesforce": "CRM",
    "oracle": "ORCL",
    "ibm": "IBM",
    "paypal": "PYPL",
    "intuit": "INTU",
    "fortinet": "FTNT",
    "servicenow": "NOW",
    "cadence": "CDNS",
    "synopsys": "SNPS",
    "ansys": "ANSS",
    
    # İletişim ve Medya
    "comcast": "CMCSA",
    "cisco": "CSCO",
    "verizon": "VZ",
    "at&t": "T",
    "t-mobile": "TMUS",
    "netflix": "NFLX",
    "charter": "CHTR",
    
    # Diğer / Biyoteknoloji / Perakende
    "amgen": "AMGN",
    "dexcom": "DXCM",
    "ross stores": "ROST",
    "msci": "MSCI"
}

# Sadece Ticker Listesi (Toplu veri çekmek gerekirse diye)
TICKER_LIST = list(set(TRACKED_STOCKS.values()))
