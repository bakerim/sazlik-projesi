import feedparser
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
import os
import time
import json
from datetime import datetime
from config import TRACKED_STOCKS, RSS_URLS, OUTPUT_FILE

# --- 1. AYARLAR VE API KURULUMU ---

# GitHub Secrets'tan API Key'i al
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("❌ HATA: GEMINI_API_KEY bulunamadı! Lütfen GitHub Secrets ayarlarını kontrol et.")
    exit()

# Gemini'yi Yapılandır
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash') # Hız ve maliyet için Flash modeli ideal

# --- 2. TEKNİK ANALİZ MOTORU ---

def get_technical_data(ticker):
    """
    Hisse için detaylı teknik verileri çeker ve hesaplar.
    """
    try:
        stock = yf.Ticker(ticker)
        # Teknik analiz için en az 6 aylık veri çekelim (SMA200 için)
        df = stock.history(period="6mo")
        
        if len(df) < 50: # Veri çok azsa analiz yapılamaz
            return None
            
        current_price = df['Close'].iloc[-1]
        
        # --- İNDİKATÖRLERİN HESAPLANMASI ---
        # RSI (14)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # SMA (Hareketli Ortalamalar)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        
        # Trend Durumu
        trend = "NÖTR"
        if current_price > df['SMA_50'].iloc[-1]:
            trend = "YÜKSELİŞ (SMA50 Üstü)"
        else:
            trend = "DÜŞÜŞ (SMA50 Altı)"
            
        return {
            "price": round(current_price, 2),
            "volume": df['Volume'].iloc[-1],
            "change_pct": round(((current_price - df['Open'].iloc[-1]) / df['Open'].iloc[-1]) * 100, 2),
            "rsi": round(df['RSI'].iloc[-1], 2),
            "trend": trend,
            "sma_50": round(df['SMA_50'].iloc[-1], 2) if not pd.isna(df['SMA_50'].iloc[-1]) else 0
        }
    except Exception as e:
        print(f"Veri hatası ({ticker}): {e}")
        return None

# --- 3. GEMINI AI ANALİSTİ ---

def ask_gemini_analyst(ticker, news_title, tech_data):
    """
    Tüm verileri Gemini'ye gönderir ve JSON formatında trade stratejisi ister.
    """
    
    prompt = f"""
    Sen uzman bir Algoritmik Swing Trader ve Risk Yöneticisisin. Aşağıdaki verileri analiz et ve bir trade kurulumu (setup) hazırla.
    
    **GİRİŞ VERİLERİ:**
    - HİSSE: {ticker}
    - GÜNCEL FİYAT: {tech_data['price']} $
    - GÜNLÜK DEĞİŞİM: %{tech_data['change_pct']}
    - RSI (14): {tech_data['rsi']}
    - TREND DURUMU: {tech_data['trend']}
    - HABER BAŞLIĞI: "{news_title}"
    
    **GÖREV:**
    Bu haberi ve teknik verileri harmanla. Haberin fiyata etkisini, RSI durumunu (aşırı alım/satım) ve trendi düşün.
    Bana SADECE aşağıdaki JSON formatında yanıt ver (Yorum veya markdown ekleme, sadece saf JSON):
    
    {{
        "karar": "AL" veya "SAT" veya "BEKLE",
        "hedef_fiyat": (Fiyat hedefi, örn: 155.50),
        "hedef_yuzde": (Mevcut fiyata göre kar potansiyeli, örn: "%5.2"),
        "stop_loss": (Zarar kes fiyatı, örn: 138.00),
        "stop_yuzde": (Zarar riski, örn: "%-2.1"),
        "kasa_yonetimi": (Portföyün yüzde kaçı girilmeli, örn: "%5"),
        "risk_odul_orani": (Örn: "1:2.5"),
        "guven_skoru": (0-100 arası bir sayı),
        "analiz_ozeti": (Tek cümlelik, vurucu analiz. Örn: 'Haber pozitif ve RSI uygun, tepki yükselişi bekleniyor.')
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Gelen yanıtı temizle (Bazen markdown ```json ... ``` ekleyebiliyor)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Gemini Hatası: {e}")
        return None

# --- 4. ANA ÇALIŞMA DÖNGÜSÜ ---

def run_news_bot():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 AI Analist Başlatılıyor (Gemini 2.0 Flash)...")
    all_signals = []
    processed_titles = set() # Aynı haberi tekrar tekrar analiz etmemek için

    for url in RSS_URLS:
        print(f"-> Kaynak taranıyor: {url}")
        feed = feedparser.parse(url)
        
        # Son 5 habere bakalım (API kotasını korumak için)
        for entry in feed.entries[:5]: 
            title = entry.title
            
            # Başlıkta takip ettiğimiz hisse var mı?
            matched_ticker = None
            for keyword, ticker in TRACKED_STOCKS.items():
                if keyword in title.lower():
                    matched_ticker = ticker
                    break
            
            if matched_ticker and title not in processed_titles:
                print(f"   BULUNDU: {matched_ticker} -> {title[:40]}...")
                processed_titles.add(title)
                
                # 1. Teknik Veriyi Çek
                tech_data = get_technical_data(matched_ticker)
                
                if tech_data:
                    # 2. Gemini'ye Sor (Analiz)
                    print("      ⏳ Gemini Analiz Ediyor...")
                    ai_analysis = ask_gemini_analyst(matched_ticker, title, tech_data)
                    
                    if ai_analysis:
                        # 3. Verileri Birleştir ve Kaydet
                        signal_data = {
                            "Tarih": datetime.now().strftime('%Y-%m-%d %H:%M'),
                            "Hisse": matched_ticker,
                            "Fiyat": tech_data['price'],
                            "RSI": tech_data['rsi'],
                            "Karar": ai_analysis.get('karar', '-'),
                            "Hedef_Fiyat": ai_analysis.get('hedef_fiyat', 0),
                            "Kazanc_Potansiyeli": ai_analysis.get('hedef_yuzde', '-'),
                            "Stop_Loss": ai_analysis.get('stop_loss', 0),
                            "Risk_Yuzdesi": ai_analysis.get('stop_yuzde', '-'),
                            "Kasa_Yonetimi": ai_analysis.get('kasa_yonetimi', '-'),
                            "Risk_Odul": ai_analysis.get('risk_odul_orani', '-'),
                            "Guven_Skoru": ai_analysis.get('guven_skoru', 0),
                            "Analiz_Ozeti": ai_analysis.get('analiz_ozeti', '-'),
                            "Haber_Baslik": title,
                            "Link": entry.link
                        }
                        
                        all_signals.append(signal_data)
                        print(f"      ✅ AI SİNYALİ: {ai_analysis['karar']} | Skor: {ai_analysis['guven_skoru']} | {ai_analysis['analiz_ozeti']}")
                        
                        # API Rate Limit'e takılmamak için kısa bekleme
                        time.sleep(2) 
                    else:
                        print("      ⚠️ AI yanıt veremedi.")
                else:
                    print("      ⚠️ Teknik veri alınamadı.")

    # --- 5. SONUÇLARI KAYDET ---
    if all_signals:
        df = pd.DataFrame(all_signals)
        # Sütun sırasını düzenle
        cols = ["Tarih", "Hisse", "Karar", "Fiyat", "Hedef_Fiyat", "Stop_Loss", "Guven_Skoru", "Kazanc_Potansiyeli", "RSI", "Analiz_Ozeti", "Kasa_Yonetimi", "Risk_Odul", "Haber_Baslik", "Link"]
        # Eğer veri içinde eksik sütun varsa hata vermemesi için kontrol
        available_cols = [c for c in cols if c in df.columns]
        df = df[available_cols]

        if os.path.exists(OUTPUT_FILE):
            df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
        else:
            df.to_csv(OUTPUT_FILE, mode='w', header=True, index=False)
            
        print(f"\nToplam {len(all_signals)} yeni AI stratejisi kaydedildi.")
    else:
        print("\nİşlem yapılacak yeni bir fırsat bulunamadı.")

if __name__ == "__main__":
    run_news_bot()
