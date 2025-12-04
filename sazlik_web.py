import pandas as pd
import yfinance as yf
import json
import os
from datetime import datetime, timedelta

# --- AYARLAR ---
ARCHIVE_FILE = 'data/news_archive.json'  # Arşiv dosyasının yolu

# 1. FONKSİYON: GEÇMİŞİ HATIRLA (HAFIZA)
def get_past_context(ticker):
    try:
        if not os.path.exists(ARCHIVE_FILE):
            return "Arşiv dosyası yok, bu ilk analiz."
            
        df = pd.read_json(ARCHIVE_FILE)
        # Tarih formatını ayarla
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            
        # Son 30 gündeki o hisseye ait haberleri getir
        cutoff_date = datetime.now() - timedelta(days=30)
        mask = (df['ticker'] == ticker) & (df['date'] > cutoff_date)
        relevant_news = df.loc[mask].sort_values(by='date', ascending=True)
        
        if relevant_news.empty:
            return "Bu hisse ile ilgili son 30 günde kayıtlı haber yok."
            
        context_text = ""
        for _, row in relevant_news.iterrows():
            d_str = row['date'].strftime('%Y-%m-%d')
            context_text += f"- [{d_str}] {row['content']} (AI Yorumu: {row.get('ai_sentiment', 'Yok')})\n"
        return context_text
    except Exception as e:
        return f"Hafıza hatası: {str(e)}"

# 2. FONKSİYON: TEKNİK ANALİZ (GÖZ)
def get_technical_status(ticker):
    try:
        # BIST kodu kontrolü (Sonunda .IS yoksa ekle)
        symbol = f"{ticker}.IS" if not ticker.endswith(".IS") else ticker
        
        stock = yf.Ticker(symbol)
        hist = stock.history(period="6mo") # Son 6 ay
        
        if hist.empty:
            return "Teknik veri çekilemedi."
            
        price = hist['Close'].iloc[-1]
        sma50 = hist['Close'].rolling(50).mean().iloc[-1]
        
        # Basit Trend Analizi
        trend = "YÜKSELİŞ (Boğa)" if price > sma50 else "DÜŞÜŞ (Ayı)"
        
        return f"Güncel Fiyat: {price:.2f} TL, Ana Trend: {trend}"
    except Exception as e:
        return f"Teknik analiz yapılamadı: {str(e)}"

# 3. FONKSİYON: PROMPT HAZIRLAYICI (BEYİN)
# İşte senin sormana gerek kalmadan, kodun kendi kendine hazırladığı prompt:
def generate_ai_prompt(ticker, news_text, context, technicals):
    system_prompt = f"""
    Sen uzman bir borsa analistisin. Aşağıdaki verileri kullanarak bu haberi yorumla.
    
    1. HİSSE: {ticker}
    2. CANLI TEKNİK DURUM: {technicals}
    3. GEÇMİŞ HABERLER (BAĞLAM):
    {context}
    
    4. YENİ HABER:
    "{news_text}"
    
    GÖREVİN:
    Bu haberin fiyata etkisini 0-100 arası puanla, yönünü (Pozitif/Negatif) belirle.
    Sadece JSON formatında cevap ver: {{ "score": 85, "sentiment": "Pozitif", "reason": "..." }}
    """
    return system_prompt

# --- ANA ÇALIŞMA ALANI (MAIN) ---
def main():
    # BURADA NORMALDE HABERİ ÇEKTİĞİN KOD OLACAK
    # Örnek olarak elimizde yeni bir haber varmış gibi davranalım:
    new_news = {
        'ticker': 'ASELS', 
        'content': 'ASELSAN, yurt dışı kaynaklı 30 Milyon Dolarlık satış sözleşmesi imzaladı.'
    }
    
    print(f"--- {new_news['ticker']} İçin Sazlık Analizi Başlıyor ---")
    
    # 1. Adım: Geçmişi getir
    context = get_past_context(new_news['ticker'])
    
    # 2. Adım: Teknik duruma bak
    technicals = get_technical_status(new_news['ticker'])
    
    # 3. Adım: Promptu oluştur (Otomatik)
    final_prompt = generate_ai_prompt(new_news['ticker'], new_news['content'], context, technicals)
    
    # 4. Adım: AI'a Gönder (Burası senin API anahtarınla çalışacak kısım)
    # Şimdilik ekrana basıyoruz ki çalıştığını gör:
    print("\n--- AI'A GİDECEK MESAJ (PROMPT) ---")
    print(final_prompt)
    print("-----------------------------------")
    
    # Not: Gerçek sistemde burada openai.ChatCompletion... kodu olacak.
    # Ve gelen cevabı veritabanına kaydedeceğiz.

if __name__ == "__main__":
    main()
