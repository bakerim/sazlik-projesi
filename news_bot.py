import yfinance as yf
import json
import os
import time
from datetime import datetime

# --- 🔥 SAZLIK AVCI LİSTESİ ---
WATCHLIST = [
    # > MUHTEŞEM 7'Lİ & TEKNOLOJİ DEVLERİ
    'NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'ADBE', 'CRM',
    'ORCL', 'CSCO', 'INTC', 'AMD', 'QCOM', 'TXN', 'AVGO', 'MU', 'LRCX', 'AMAT',
    
    # > YÜKSEK VOLATİLİTE & YAPAY ZEKA (Swing Cenneti)
    'PLTR', 'AI', 'SMCI', 'ARM', 'PATH', 'SNOW', 'DDOG', 'CRWD', 'PANW', 'ZS',
    'NET', 'MDB', 'TEAM', 'U', 'DKNG', 'ROKU', 'SQ', 'SHOP', 'PYPL', 'HOOD',
    
    # > KRİPTO & BLOCKCHAIN (Bitcoin Hareketleri)
    'COIN', 'MSTR', 'MARA', 'RIOT', 'CLSK', 'HUT', 'BITF',
    
    # > ELEKTRİKLİ ARAÇ & ENERJİ
    'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'FSLR', 'ENPH', 'SEDG', 'PLUG', 'FCEL',
    
    # > FİNANS & BANKACILIK (Hacim Depoları)
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'V', 'MA', 'AXP',
    
    # > PERAKENDE & TÜKETİM (Bilanço Dönemleri İçin)
    'WMT', 'TGT', 'COST', 'HD', 'LOW', 'NKE', 'LULU', 'SBUX', 'MCD', 'KO',
    
    # > SAĞLIK & BİYOTEKNOLOJİ (Haber Odaklı)
    'LLY', 'NVO', 'PFE', 'MRNA', 'BNTX', 'VRTX', 'REGN', 'GILD', 'AMGN', 'ISRG',
    
    # > ENDÜSTRİ & SAVUNMA
    'BA', 'LMT', 'RTX', 'GE', 'CAT', 'DE', 'HON', 'UNP', 'UPS', 'FDX',
    
    # > ÇİN & GELİŞMEKTE OLANLAR (Riskli ama Karlı)
    'BABA', 'PDD', 'BIDU', 'JD', 'TCEHY',
    
    # > DİĞER POPÜLER HİSSELER
    'DIS', 'CMCSA', 'TMUS', 'VZ', 'T', 'F', 'GM', 'UBER', 'ABNB', 'DASH'
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
    """
    Yahoo'nun karışık veri yapısını çözen akıllı fonksiyon.
    Hem düz yapıyı hem de 'content' içine gömülü yapıyı dener.
    """
    title = None
    link = None
    date_str = datetime.now().strftime('%Y-%m-%d') # Varsayılan: Bugün

    # 1. BAŞLIK VE LİNKİ BULMA
    # Yöntem A: Düz Yapı
    if 'title' in news_item:
        title = news_item['title']
        link = news_item.get('link')
    
    # Yöntem B: İç İçe Yapı (Senin yakaladığın durum)
    elif 'content' in news_item:
        content = news_item['content']
        title = content.get('title')
        # Link bazen 'clickThroughUrl' içindedir
        if 'clickThroughUrl' in content:
            link = content['clickThroughUrl'].get('url')
    
    if not title:
        return None # Başlık yoksa bu veriyi atla

    # 2. TARİHİ BULMA
    # Yöntem A: Unix Timestamp
    if 'providerPublishTime' in news_item:
        ts = news_item['providerPublishTime']
        date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    
    # Yöntem B: ISO String (Örn: 2025-12-05T13:00:07Z)
    elif 'content' in news_item and 'pubDate' in news_item['content']:
        raw_date = news_item['content']['pubDate']
        try:
            # Sadece ilk 10 karakteri (YYYY-MM-DD) alıp işi çözelim
            date_str = raw_date[:10]
        except:
            pass

    return {
        "title": title,
        "link": link,
        "date": date_str
    }

def fetch_sweet_spots():
    print(f"🇺🇸 ABD Botu (Akıllı Mod) Başlatıldı...")
    
    archive_data = load_archive()
    existing_fingerprints = {f"{item.get('ticker')}_{item.get('content')}" for item in archive_data}
    
    total_new = 0
    
    for ticker in WATCHLIST:
        print(f"\n🔍 {ticker} taranıyor...")
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            if not news_list:
                print(f"   ⚠️ Liste boş.")
                continue
            
            count = 0
            for raw_news in news_list:
                # Veriyi akıllı fonksiyona gönderip temiz halini alalım
                clean_data = parse_news_data(raw_news)
                
                if not clean_data:
                    continue

                # Parmak izi kontrolü (Aynı haberi kaydetme)
                fingerprint = f"{ticker}_{clean_data['title']}"
                
                # Tarih Kontrolü (Son 30 gün)
                try:
                    news_dt = datetime.strptime(clean_data['date'], '%Y-%m-%d')
                    days_diff = (datetime.now() - news_dt).days
                    if days_diff > 30:
                        continue
                except:
                    pass

                if fingerprint not in existing_fingerprints:
                    entry = {
                        "date": clean_data['date'],
                        "ticker": ticker,
                        "content": clean_data['title'],
                        "link": clean_data['link'],
                        "ai_sentiment": "Analiz Bekliyor"
                    }
                    archive_data.append(entry)
                    existing_fingerprints.add(fingerprint)
                    total_new += 1
                    count += 1
                    print(f"   ✅ [KAYDEDİLDİ] {clean_data['date']}: {clean_data['title'][:40]}...")
            
            if count == 0:
                print("   ℹ️ Yeni kayıt yok (Hepsi eski veya zaten var).")
                
            time.sleep(1) 
                    
        except Exception as e:
            print(f"   ❌ Hata: {e}")

    # KAYIT
    if total_new > 0:
        print(f"\n💾 Toplam {total_new} yeni haber arşive yazılıyor...")
        archive_data.sort(key=lambda x: x['date'], reverse=True)
        save_archive(archive_data)
    else:
        print("\n💤 Değişiklik yok.")

if __name__ == "__main__":
    fetch_sweet_spots()
