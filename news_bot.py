import yfinance as yf
import json
import os
import time
from datetime import datetime

# --- SAZLIK AVCI LİSTESİ ---
WATCHLIST = [
    'NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'AMD', 
    'COIN', 'MSTR', 'PLTR', 'INTC'
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

def fetch_sweet_spots():
    print(f"🇺🇸 ABD Botu Başlatıldı... Hedef: {len(WATCHLIST)} Hisse")
    
    archive_data = load_archive()
    existing_fingerprints = {f"{item.get('ticker')}_{item.get('content')}" for item in archive_data}
    
    total_found = 0
    
    for ticker in WATCHLIST:
        print(f"\n🔍 {ticker} taranıyor...")
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            # Hata Ayıklama: Liste boş mu?
            if not news_list:
                print(f"   ⚠️ {ticker} için haber listesi BOŞ döndü. (API engeli veya veri yok)")
                continue
            
            count_per_stock = 0
            for news in news_list:
                title = news.get('title')
                link = news.get('link')
                pub_time = news.get('providerPublishTime')
                
                if not pub_time or not title: 
                    continue
                
                # FİLTREYİ GEVŞETTİK: SON 14 GÜN
                news_date = datetime.fromtimestamp(pub_time)
                days_diff = (datetime.now() - news_date).days
                
                if days_diff > 14: # 3 yerine 14 yaptık
                    # Çok eski haberleri terminale basalım ki çalıştığını görelim
                    # print(f"   [Eski] {days_diff} günlük haber atlandı.") 
                    continue

                fingerprint = f"{ticker}_{title}"
                
                if fingerprint not in existing_fingerprints:
                    entry = {
                        "date": news_date.strftime('%Y-%m-%d'),
                        "ticker": ticker,
                        "content": title,
                        "link": link,
                        "ai_sentiment": "Analiz Bekliyor"
                    }
                    archive_data.append(entry)
                    existing_fingerprints.add(fingerprint)
                    total_found += 1
                    count_per_stock += 1
                    print(f"   ✅ [KAYDEDİLDİ] {title[:40]}...")
            
            if count_per_stock == 0:
                print("   ℹ️ Yeni haber yok (Tüm haberler ya eski ya da zaten kayıtlı).")
                
            time.sleep(1) # API engelini aşmak için bekleme
                    
        except Exception as e:
            print(f"   ❌ Kritik Hata ({ticker}): {e}")

    # SONUÇ
    if total_found > 0:
        print(f"\n💾 Toplam {total_found} yeni haber bulundu ve arşive yazılıyor...")
        archive_data.sort(key=lambda x: x['date'], reverse=True)
        save_archive(archive_data)
    else:
        print("\n💤 Hiçbir yeni haber bulunamadı. Dosya değiştirilmiyor.")

if __name__ == "__main__":
    fetch_sweet_spots()
