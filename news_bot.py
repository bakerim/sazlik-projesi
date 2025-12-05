import yfinance as yf
import json
import os
import time

# Sadece tek bir hisseye bakalım, sorunu anlamak için yeterli
WATCHLIST = ['NVDA']

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
    print(f"🔍 RÖNTGEN MODU BAŞLATILDI (Veri Yapısı Analizi)...")
    
    archive_data = load_archive()
    
    for ticker in WATCHLIST:
        print(f"\n🔬 {ticker} inceleniyor...")
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            if not news_list:
                print("   ⚠️ Liste tamamen boş.")
                continue
            
            print(f"   -> {len(news_list)} adet veri paketi yakalandı.")
            
            # --- İŞTE BURASI ÖNEMLİ ---
            # İlk haberin İÇİNDEKİ her şeyi ekrana dökelim
            first_news = news_list[0]
            print("\n🚨 [KRİTİK BİLGİ] İLK HABERİN HAM YAPISI:")
            print(json.dumps(first_news, indent=4))
            print("--------------------------------------------------\n")
            
            # Şimdi körlemesine kaydetmeyi deneyelim (Başlık olmasa bile)
            for news in news_list:
                # Başlık 'title' değilse 'headline' olabilir, hepsini deneyelim
                title = news.get('title') or news.get('headline') or "BAŞLIK BULUNAMADI"
                link = news.get('link') or "Link Yok"
                
                # Parmak izi kontrolü
                fingerprint = f"{ticker}_{title}"
                exists = any(f"{item['ticker']}_{item['content']}" == fingerprint for item in archive_data)
                
                if not exists:
                    entry = {
                        "date": "2024-12-05", # Şimdilik tarihi boşver, veri akışını görelim
                        "ticker": ticker,
                        "content": title,
                        "link": link,
                        "ai_sentiment": "Test Verisi"
                    }
                    archive_data.append(entry)
                    print(f"   ✅ Zorla Kaydedildi: {title[:30]}...")

        except Exception as e:
            print(f"   ❌ Hata: {e}")

    # Kaydet
    if len(archive_data) > 0:
        save_archive(archive_data)
        print("\n💾 Arşiv dosyası güncellendi.")

if __name__ == "__main__":
    fetch_sweet_spots()
