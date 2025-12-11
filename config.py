# config.py

# Takip edilecek Haber Kaynakları (RSS)
RSS_URLS = [
    "https://finance.yahoo.com/news/rssindex",
    "http://feeds.marketwatch.com/marketwatch/marketpulse",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"
]

# Takip Listesi ve İsim Eşleştirmeleri
TRACKED_STOCKS = {
    # Teknoloji Devleri
    "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL",
    "amazon": "AMZN", "nvidia": "NVDA", "meta": "META", "facebook": "META",
    "tesla": "TSLA",
    # Çip ve Donanım
    "broadcom": "AVGO", "qualcomm": "QCOM", "intel": "INTC", "amd": "AMD",
    "micron": "MU", "texas instruments": "TXN", "analog devices": "ADI",
    # Yazılım ve Servisler
    "adobe": "ADBE", "salesforce": "CRM", "oracle": "ORCL", "ibm": "IBM",
    "paypal": "PYPL", "netflix": "NFLX",
    # Diğer
    "cisco": "CSCO", "at&t": "T", "disney": "DIS"
}

# Sonuçların Kaydedileceği Dosya Adı
OUTPUT_FILE = "sazlik_signals.csv"
