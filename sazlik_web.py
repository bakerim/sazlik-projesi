print("1. Başlangıç: Program başlatılıyor...")

try:
    print("2. Kütüphaneler yükleniyor (Bu biraz sürebilir)...")
    import pandas as pd
    import yfinance as yf
    import json
    import os
    from datetime import datetime, timedelta
    print("3. Kütüphaneler başarıyla yüklendi!")
except ImportError as e:
    print(f"HATA: Kütüphane eksik! Lütfen 'pip install pandas yfinance' yapın. Hata detayı: {e}")
    exit()

# --- AYARLAR ---
ARCHIVE_FILE = 'data/news_archive.json'

def get_technical_status(ticker):
    print(f"   -> '{ticker}' için teknik veri çekiliyor...")
    try:
        symbol = f"{ticker}.IS" if not ticker.endswith(".IS") else ticker
        stock = yf.Ticker(symbol)
        
        # Sadece son 5 günlük veriyi çekelim ki hızlı olsun
        hist = stock.history(period="5d") 
        
        if hist.empty:
            print("   -> UYARI: Teknik veri boş geldi.")
            return "Veri yok"
            
        price = hist['Close'].iloc[-1]
        print(f"   -> Fiyat bulundu: {price}")
        return f"Fiyat: {price:.2f} TL"
    except Exception as e:
        print(f"   -> HATA (Teknik): {e}")
        return f"Hata: {str(e)}"

def main():
    print("4. Ana fonksiyon çalıştı.")
    
    ticker = 'ASELS'
    print(f"5. {ticker} analizi başlıyor.")
    
    # Teknik analiz fonksiyonunu çağır
    technicals = get_technical_status(ticker)
    
    print("6. Sonuçlar derleniyor...")
    print("\n--- SONUÇ ---")
    print(f"Hisse: {ticker}")
    print(f"Durum: {technicals}")
    print("7. Program başarıyla bitti.")

if __name__ == "__main__":
    main()
