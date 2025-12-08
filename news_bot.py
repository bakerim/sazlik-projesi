import yfinance as yf
import json
import os
import time
import random
from datetime import datetime
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- NLTK VADER Kurulumu (İlk çalışmada indirir) ---
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

# Sentiment Motorunu Başlat
analyzer = SentimentIntensityAnalyzer()

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

ARCHIVE_FILE = 'news_archive.json'

def load_archive():
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_archive(data):
    with open(ARCHIVE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def analyze_sentiment(text):
    """Metni analiz eder ve Duygu Durumunu döndürür."""
    if not text: return "Nötr 😐", 0
    
    # VADER Skorlaması (-1 ile +1 arası)
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    if compound >= 0.05:
        return "Olumlu 🟢", compound
    elif compound <= -0.05:
        return "Olumsuz 🔴", compound
    else:
        return "Nötr ⚪", compound

def parse_news_data(news_item):
    title = None
    link = None
    date_str = datetime.now().strftime('%Y-%m-%d')

    if 'title' in news_item:
        title = news_item['title']
        link = news_item.get('link')
    elif 'content' in news_item:
        content = news_item['content']
        title = content.get('title')
        if 'clickThroughUrl' in content:
            link = content['clickThroughUrl'].get('url')
    
    if not title: return None

    # Tarih Çözümleme
    if 'providerPublishTime' in news_item:
        date_str = datetime.fromtimestamp(news_item['providerPublishTime']).strftime('%Y-%m-%d')
    
    return {"title": title, "link": link, "date": date_str}

def fetch_sweet_spots():
    print(f"🇺🇸 Sazlık Haber Botu + AI Sentiment Başlatılıyor...")
    
    archive_data = load_archive()
    existing_fingerprints = {f"{item.get('ticker')}_{item.get('content')}" for item in archive_data}
    
    total_new = 0
    
    # Listeyi karıştır (Her seferinde aynı sırayla gidip ban yemeyelim)
    random.shuffle(WATCHLIST)
    
    for ticker in WATCHLIST:
        print(f"📰 {ticker}...", end=" ", flush=True)
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            if not news_list:
                print("📭", end=" ") 
                time.sleep(random.uniform(1, 2))
                continue
            
            count = 0
            for raw_news in news_list:
                clean = parse_news_data(raw_news)
                if not clean: continue

                # --- 30 GÜN KURALI (BURAYI GÜNCELLEDİK) ---
                try:
                    # Tarih formatı bazen değişebilir, o yüzden try-except şart
                    news_dt = datetime.strptime(clean['date'], '%Y-%m-%d')
                    days_diff = (datetime.now() - news_dt).days
                    
                    if days_diff > 30: # 30 Günden eski haberi alma!
                        continue
                except: 
                    pass # Tarih hesaplanamazsa haberi al (Güvenli taraf)

                fingerprint = f"{ticker}_{clean['title']}"
                
                if fingerprint not in existing_fingerprints:
                    # Sentiment Analizi
                    sentiment_label, sentiment_score = analyze_sentiment(clean['title'])
                    
                    entry = {
                        "date": clean['date'],
                        "ticker": ticker,
                        "content": clean['title'],
                        "link": clean['link'],
                        "ai_sentiment": sentiment_label,
                        "sentiment_score": sentiment_score
                    }
                    archive_data.append(entry)
                    existing_fingerprints.add(fingerprint)
                    total_new += 1
                    count += 1
            
            if count > 0: print(f"✅ {count} Yeni Haber")
            else: print("💤")
            
            time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"❌")
            time.sleep(3)

        # Her 10 hissede bir kaydet (Veri kaybını önlemek için)
        if total_new > 0 and total_new % 5 == 0:
             save_archive(archive_data)

    # Döngü bitince son kayıt
    if total_new > 0:
        archive_data.sort(key=lambda x: x['date'], reverse=True)
        save_archive(archive_data)
        print(f"\n💾 TOPLAM {total_new} YENİ HABER VE ANALİZİ KAYDEDİLDİ.")
    else:
        print("\n💤 Yeni haber yok.")

if __name__ == "__main__":
    fetch_sweet_spots()