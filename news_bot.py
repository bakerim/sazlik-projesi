import yfinance as yf
import pandas as pd
import json
import os
import time
from datetime import datetime

# --- 🔥 SAZLIK AVCI LİSTESİ (PASTANIN EN TATLI YERİ) ---
# Swing Trade için hacmi yüksek, habere duyarlı ve agresif hisseler.
WATCHLIST = [
    # > TEKNOLOJİ DEVLERİ (Piyasa Yapıcılar)
    'NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX',
    
    # > YARI İLETKEN & ÇİP (En Yüksek Volatilite Buradadır)
    'AMD', 'INTC', 'ARM', 'QCOM', 'MU', 'AVGO', 'TSM', 'SMCI',
    
    # > KRİPTO & FINTECH (Bitcoin Hareketine Duyarlı)
    'COIN', 'MSTR', 'MARA', 'RIOT', 'HOOD', 'PYPL', 'SQ',
    
    # > YAPAY ZEKA & YAZILIM (Büyüme Odaklı)
    'PLTR', 'SNOW', 'CRWD', 'PANW', 'ORCL', 'ADBE', 'CRM', 'PATH',
    
    # > ELEKTRİKLİ ARAÇ & ENERJİ (Gelecek Vizyonu)
    'RIVN', 'LCID', 'NIO', 'FSLR', 'ENPH',
    
    # > ÇİN DEVLERİ (Yüksek Risk/Getiri)
    'BABA', 'PDD', 'BIDU'
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
    print(f"🇺🇸 ABD Borsası Taranıyor... Hedef: {len(WATCHLIST)} Agresif Hisse")
    
    archive_data = load_archive()
    
    # Mükerrer kayıt önlemek için mevcut başlıkları hafızaya al
    existing_fingerprints = {f"{item['ticker']}_{item['content']}" for item in archive_data}
    
    new_entries_count = 0
    
    # Hepsini tek seferde çekmek yerine hisse hisse geziyoruz
    for ticker in WATCHLIST:
        try:
            # Ticker nesnesi oluştur
            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            if not news_list:
                continue
                
            print(f" -> {ticker} sinyalleri kontrol ediliyor...")
            
            for news in news_list:
                title = news.get('title')
                link = news.get('link')
                pub_time = news.get('providerPublishTime')
                
                # Tarih damgası yoksa atla
                if not pub_time: continue
                
                date_str = datetime.fromtimestamp(pub_time).strftime('%Y-%m-%d')
                
                # Sadece SON 3 GÜNÜN haberlerini al (Çok eski haber bayattır)
                news_date = datetime.fromtimestamp(pub_time)
                days_diff = (datetime.now() - news_date).days
                if days_diff > 3:
                    continue

                # Benzersiz kimlik oluştur
                fingerprint = f"{ticker}_{title}"
                
                if title and fingerprint not in existing_fingerprints:
                    entry = {
                        "date": date_str,
                        "ticker": ticker,
                        "content": title,
                        "link": link,
                        "ai_sentiment": "Analiz Bekliyor", # Henüz AI bakmadı
                        "crawled_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    archive_data.append(entry)
                    existing_fingerprints.add(fingerprint)
                    new_entries_count += 1
                    print(f"    🔥 [YENİ] {ticker}: {title[:40]}...")
            
            # API'yi boğmamak için minik bir nefes al
            time.sleep(0.5)
                    
        except Exception as e:
            print(f"    ⚠️ Hata ({ticker}): {e}")

    # Değişiklik varsa kaydet
    if new_entries_count > 0:
        # En yeni tarih en üstte olacak şekilde sırala
        archive_data.sort(key=lambda x: x['date'], reverse=True)
        save_archive(archive_data)
        print(f"\n✅ Operasyon Tamamlandı: {new_entries_count} taze haber 'Hafıza'ya eklendi.")
    else:
        print("\n💤 Piyasa sakin, yeni 'kaymaklı' haber yok.")

if __name__ == "__main__":
    fetch_sweet_spots()
