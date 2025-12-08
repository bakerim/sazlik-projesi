import yfinance as yf
import json
import os
import time
from datetime import datetime

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
WATCHLIST.sort() # Alfabetik sıralama (Logları okumak kolay olsun)

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

def parse_news_data(news_item):
    """Yahoo'nun karmaşık veri yapısını çözen fonksiyon"""
    title = None
    link = None
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Başlık ve Link Bulma (Farklı yapıları dener)
    if 'title' in news_item:
        title = news_item['title']
        link = news_item.get('link')
    elif 'content' in news_item:
        content = news_item['content']
        title = content.get('title')
        if 'clickThroughUrl' in content:
            link = content['clickThroughUrl'].get('url')
    
    if not title: return None

    # Tarih Bulma
    if 'providerPublishTime' in news_item:
        ts = news_item['providerPublishTime']
        date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    elif 'content' in news_item and 'pubDate' in news_item['content']:
        try:
            date_str = news_item['content']['pubDate'][:10]
        except: pass
    
    return {"title": title, "link": link, "date": date_str}

def fetch_sweet_spots():
    print(f"🇺🇸 Sazlık 500 Botu Başlatıldı ({len(WATCHLIST)} Hisse)...")
    print(f"📅 Tarama Aralığı: Son 10 Gün")
    
    archive_data = load_archive()
    # Parmak izi kümesi oluştur (Hız için)
    existing_fingerprints = {f"{item.get('ticker')}_{item.get('content')}" for item in archive_data}
    
    total_new = 0
    
    for ticker in WATCHLIST:
        print(f"🔍 {ticker}...", end=" ", flush=True)
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            if not news_list:
                print("⚠️ Boş (Veri Yok)")
                time.sleep(1) # Boş olsa bile bekle
                continue
            
            count = 0
            for raw_news in news_list:
                clean = parse_news_data(raw_news)
                if not clean: continue

                # --- 10 GÜN KURALI ---
                try:
                    news_dt = datetime.strptime(clean['date'], '%Y-%m-%d')
                    days_diff = (datetime.now() - news_dt).days
                    if days_diff > 10: # 10 Günden eskiyi alma
                        continue
                except: pass

                fingerprint = f"{ticker}_{clean['title']}"
                
                # Eğer bu haber daha önce kaydedilmemişse ekle
                if fingerprint not in existing_fingerprints:
                    entry = {
                        "date": clean['date'],
                        "ticker": ticker,
                        "content": clean['title'],
                        "link": clean['link'],
                        "ai_sentiment": "Analiz Bekliyor"
                    }
                    archive_data.append(entry)
                    existing_fingerprints.add(fingerprint)
                    total_new += 1
                    count += 1
            
            if count > 0: print(f"✅ {count} Yeni")
            else: print("💤 (Güncel)")
            
            # --- HIZ AYARI (BAN YEMEMEK İÇİN) ---
            bekleme_suresi = random.uniform(3.5, 6.5) 
            time.sleep(bekleme_suresi) 
        
    except Exception as e:
        # Hata aldığınızda daha uzun bekleme süresi
        print(f"❌ Hata. Bir sonraki denemeye geçiliyor. Sebep: {e}")
        time.sleep(5) 
        continue

        except Exception as e:
            print(f"❌ Hata")
            time.sleep(2) # Hata alsa bile bekle

    if total_new > 0:
        # Tarihe göre sırala (En yeni en üstte)
        archive_data.sort(key=lambda x: x['date'], reverse=True)
        save_archive(archive_data)
        print(f"\n💾 TOPLAM {total_new} YENİ HABER ARŞİVE EKLENDİ.")
    else:
        print("\n💤 Değişiklik yok, veriler güncel.")

if __name__ == "__main__":
    fetch_sweet_spots()
