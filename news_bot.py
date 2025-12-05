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
    print(f"🇺🇸 ABD Botu (Debug Modu) Başlatıldı...")
    
    archive_data = load_archive()
    # Parmak izlerini oluştur
    existing_fingerprints = {f"{item.get('ticker')}_{item.get('content')}" for item in archive_data}
    
    total_found = 0
    
    for ticker in WATCHLIST:
        print(f"\n🔍 {ticker} taranıyor...")
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            # 1. HATA KONTROLÜ: LİSTE BOŞ MU?
            if not news_list:
                print(f"   ⚠️ {ticker} için haber listesi BOŞ geldi. (Yahoo veriyi vermedi)")
                continue
            
            print(f"   -> {len(news_list)} adet ham veri bulundu. Filtreleniyor...")
            
            count_per_stock = 0
            for news in news_list:
                title = news.get('title')
                link = news.get('link')
                pub_time = news.get('providerPublishTime')
                
                if not title: 
                    continue
                
                # Tarih Kontrolü
                news_date = datetime.now() # Varsayılan
                days_diff = 0
                
                if pub_time:
                    news_date = datetime.fromtimestamp(pub_time)
                    days_diff = (datetime.now() - news_date).days
                    # DEBUG BASKISI: Tarihi görelim
                    print(f"      - Haber Tarihi: {news_date.strftime('%Y-%m-%d')} ({days_diff} gün önce)")
                else:
                    print("      - Tarih verisi yok, yine de alınıyor.")

                # FİLTREYİ GEVŞETTİK: 60 GÜN (2 AY)
                if days_diff > 60: 
                    print(f"        -> Çok eski, atlandı.")
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
                    print(f"      ✅ EKLENDİ: {title[:30]}...")
            
            if count_per_stock == 0:
                print("   ℹ️ Bu hisse için uygun yeni kayıt çıkmadı.")
                
            time.sleep(1) 
                    
        except Exception as e:
            print(f"   ❌ Hata ({ticker}): {e}")

    # SONUÇ
    if total_found > 0:
        print(f"\n💾 Toplam {total_found} yeni haber bulundu ve arşive yazılıyor...")
        # En yeniden en eskiye sırala
        archive_data.sort(key=lambda x: x['date'], reverse=True)
        save_archive(archive_data)
    else:
        print("\n💤 Hiçbir yeni kayıt yapılamadı.")

if __name__ == "__main__":
    fetch_sweet_spots()
