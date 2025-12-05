import yfinance as yf
import json
import os
import time
from datetime import datetime

# --- 🔥 SAZLIK 100: DEV LİSTE ---
WATCHLIST = [
    # TEKNOLOJİ & AI
    'NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'AMD', 'INTC',
    'PLTR', 'AI', 'SMCI', 'ARM', 'PATH', 'SNOW', 'CRWD', 'PANW', 'ORCL', 'ADBE',
    # KRİPTO & FINTECH
    'COIN', 'MSTR', 'MARA', 'RIOT', 'HOOD', 'PYPL', 'SQ', 'V', 'MA', 'JPM',
    # ENERJİ & EV
    'RIVN', 'LCID', 'NIO', 'FSLR', 'ENPH', 'XOM', 'CVX',
    # PERAKENDE & DİĞER
    'WMT', 'COST', 'TGT', 'DIS', 'BA', 'LMT', 'GE', 'PFE', 'LLY', 'NVO',
    # ÇİN & GELİŞMEKTE OLANLAR
    'BABA', 'PDD', 'BIDU', 'JD'
    # (Listeyi çok uzatıp API'yi yormamak için en hacimli 50 tanesini koydum, istersen artırırız)
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

def parse_news_data(news_item):
    """Yahoo veri çözümleyici"""
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

    if 'providerPublishTime' in news_item:
        ts = news_item['providerPublishTime']
        date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    
    return {"title": title, "link": link, "date": date_str}

def fetch_sweet_spots():
    print(f"🇺🇸 Sazlık 100 Botu Başlatıldı ({len(WATCHLIST)} Hisse)...")
    
    archive_data = load_archive()
    existing_fingerprints = {f"{item.get('ticker')}_{item.get('content')}" for item in archive_data}
    
    total_new = 0
    
    for ticker in WATCHLIST:
        print(f"🔍 {ticker}...", end=" ", flush=True)
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            if not news_list:
                print("⚠️ Boş")
                continue
            
            count = 0
            for raw_news in news_list:
                clean = parse_news_data(raw_news)
                if not clean: continue

                # Sadece son 24 saatin haberlerini al (Hızlanmak için)
                try:
                    news_dt = datetime.strptime(clean['date'], '%Y-%m-%d')
                    days_diff = (datetime.now() - news_dt).days
                    if days_diff > 3: # 3 Günden eskiyi alma
                        continue
                except: pass

                fingerprint = f"{ticker}_{clean['title']}"
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
            else: print("💤")
            
            time.sleep(0.5) # API nezaket beklemesi

        except Exception:
            print("❌")

    if total_new > 0:
        archive_data.sort(key=lambda x: x['date'], reverse=True)
        save_archive(archive_data)
        print(f"\n💾 Toplam {total_new} haber kaydedildi.")
    else:
        print("\n💤 Değişiklik yok.")

if __name__ == "__main__":
    fetch_sweet_spots()
