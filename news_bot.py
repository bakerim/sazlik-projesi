import yfinance as yf
import json
import os
import time
from datetime import datetime

# --- 🔥 SAZLIK 100: DEV LİSTE ---
WATCHLIST = [
    'NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'AMD', 'INTC',
    'PLTR', 'AI', 'SMCI', 'ARM', 'PATH', 'SNOW', 'CRWD', 'PANW', 'ORCL', 'ADBE',
    'COIN', 'MSTR', 'MARA', 'RIOT', 'HOOD', 'PYPL', 'SQ', 'V', 'MA', 'JPM',
    'RIVN', 'LCID', 'NIO', 'FSLR', 'ENPH', 'XOM', 'CVX',
    'WMT', 'COST', 'TGT', 'DIS', 'BA', 'LMT', 'GE', 'PFE', 'LLY', 'NVO',
    'BABA', 'PDD', 'BIDU', 'JD', 'CSCO', 'TXN', 'AVGO', 'MU', 'LRCX', 'AMAT',
    'DDOG', 'ZS', 'NET', 'MDB', 'TEAM', 'U', 'DKNG', 'ROKU', 'SHOP',
    'CLSK', 'HUT', 'BITF', 'XPEV', 'LI', 'SEDG', 'PLUG', 'FCEL',
    'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'AXP',
    'HD', 'LOW', 'NKE', 'LULU', 'SBUX', 'MCD', 'KO',
    'MRNA', 'BNTX', 'VRTX', 'REGN', 'GILD', 'AMGN', 'ISRG',
    'RTX', 'CAT', 'DE', 'HON', 'UNP', 'UPS', 'FDX', 'CMCSA', 'TMUS', 'VZ', 'T', 'F', 'GM', 'UBER', 'ABNB', 'DASH'
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
    print(f"🇺🇸 Sazlık 100 Botu Başlatıldı ({len(WATCHLIST)} Hisse)...")
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
            time.sleep(2) # 2 Saniye bekle (Önceki 0.5 idi, şimdi daha güvenli)

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
