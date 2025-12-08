import yfinance as yf
import pandas as pd
import numpy as np
import time
import random

# --- 🎯 HEDEF LİSTE (Test için kısa tuttum, 500'lük listeyi buraya yapıştırırsın) ---
# Not: Çoklu analiz yavaştır, yfinance 'info' verisi her hisse için ayrı istek atar.
WATCHLIST = ["AAPL", "MSFT", "TSLA", "NVDA", "JPM", "KO", "AMD", "GOOGL"]

def calculate_rsi(series, period=14):
    """Göreceli Güç Endeksi (RSI) Hesaplar - Teknik Gösterge"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_financial_data(ticker_symbol):
    """
    Hem TEMEL (Bilanço) hem de TEKNİK (Fiyat) verilerini çeker ve analiz eder.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # --- 1. TEKNİK ANALİZ VERİLERİ (Hızlı) ---
        # Son 1 yıllık veriyi çek
        hist = stock.history(period="1y")
        
        if hist.empty: return None
        
        current_price = hist['Close'].iloc[-1]
        
        # Hareketli Ortalamalar (Trend)
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        
        # RSI (Momentum)
        rsi_val = calculate_rsi(hist['Close']).iloc[-1]
        
        # Teknik Puanlama (Basit Mantık)
        tech_score = 0
        trend_status = "Nötr"
        
        if current_price > sma_200: 
            tech_score += 20 # Uzun vadeli trend pozitif
            trend_status = "Yükseliş (Boğa)"
        if current_price > sma_50: 
            tech_score += 10 # Orta vadeli trend pozitif
        if 30 < rsi_val < 70: 
            tech_score += 10 # RSI sağlıklı bölgede
        elif rsi_val < 30:
            tech_score += 15 # RSI aşırı satımda (Alım fırsatı olabilir)

        # --- 2. TEMEL ANALİZ VERİLERİ (Yavaş - info isteği) ---
        # Not: yfinance.info bazen yavaş yanıt verir veya boş döner.
        info = stock.info
        
        # Kritik Oranlar
        pe_ratio = info.get('forwardPE', 0) # Fiyat/Kazanç (Gelecek tahmini)
        debt_equity = info.get('debtToEquity', 0) # Borç/Özkaynak
        profit_margins = info.get('profitMargins', 0) # Kar Marjı
        
        fund_score = 0
        
        # Temel Puanlama (Garantici Baba Kriterleri)
        if pe_ratio > 0 and pe_ratio < 25: 
            fund_score += 20 # Makul değerleme
        if debt_equity < 150: # %150'den az borç (Sektöre göre değişir ama genel kural)
            fund_score += 15 
        if profit_margins > 0.10: # %10'dan fazla net kar marjı
            fund_score += 15

        # --- SONUÇ ---
        total_score = tech_score + fund_score
        
        return {
            "Sembol": ticker_symbol,
            "Fiyat": round(current_price, 2),
            "Sazlık_Skoru": total_score,
            "Trend": trend_status,
            "RSI": round(rsi_val, 2),
            "F/K (P/E)": round(pe_ratio, 2) if pe_ratio else "N/A",
            "Borç Durumu": "Yüksek" if debt_equity > 150 else "Makul",
            "Karar": "GÜÇLÜ ADAY" if total_score > 70 else "İZLE"
        }

    except Exception as e:
        print(f"⚠️ Hata ({ticker_symbol}): {e}")
        return None

def main_analysis():
    print("🚀 Sazlık Analiz Motoru Başlatılıyor...")
    print(f"📊 Toplam {len(WATCHLIST)} hisse taranacak.\n")
    
    results = []
    
    for ticker in WATCHLIST:
        print(f"🔍 Analiz ediliyor: {ticker}...", end=" ", flush=True)
        
        data = get_financial_data(ticker)
        
        if data:
            results.append(data)
            print(f"✅ Bitti (Skor: {data['Sazlık_Skoru']})")
        else:
            print("❌ Veri alınamadı")
        
        # Yahoo Finance Ban Koruması (Rastgele Bekleme)
        time.sleep(random.uniform(2, 4))
    
    # Sonuçları DataFrame'e çevir ve Sırala
    df = pd.DataFrame(results)
    
    if not df.empty:
        df = df.sort_values(by="Sazlık_Skoru", ascending=False)
        print("\n" + "="*50)
        print("🏆 SAZLIK PROJESİ: ANALİZ SONUÇLARI")
        print("="*50)
        print(df.to_string(index=False))
        
        # İstersen CSV olarak kaydet
        df.to_csv("sazlik_analiz_sonuclari.csv", index=False)
        print("\n💾 Sonuçlar 'sazlik_analiz_sonuclari.csv' dosyasına kaydedildi.")
    else:
        print("\n⚠️ Hiçbir sonuç üretilemedi.")

if __name__ == "__main__":
    main_analysis()
