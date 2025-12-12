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

# --- AYARLAR ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("❌ HATA: GEMINI_API_KEY bulunamadı!")
    exit()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- TEKNİK ANALİZ ---
def get_technical_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if len(df) < 50: return None
        
        current_price = df['Close'].iloc[-1]
        df.ta.rsi(length=14, append=True)
        df.ta.sma(length=50, append=True)
        
        return {
            "price": round(current_price, 2),
            "change_pct": round(((current_price - df['Open'].iloc[-1]) / df['Open'].iloc[-1]) * 100, 2),
            "rsi": round(df['RSI_14'].iloc[-1], 2),
            "trend": "YÜKSELİŞ" if current_price > df['SMA_50'].iloc[-1] else "DÜŞÜŞ",
            "sma_50": round(df['SMA_50'].iloc[-1], 2)
        }
    except:
        return None

# --- AI ANALİST ---
def ask_gemini_consolidated(ticker, news_list, tech_data):
    # Haberleri birleştir
    news_text = "\n".join([f"- {n}" for n in news_list])
    
    prompt = f"""
    Sen acımasız ve garantici bir Hedge Fon Yöneticisisin. Aşağıdaki hisse için TOPLU bir analiz yap.
    
    HİSSE: {ticker}
    TEKNİK DURUM: Fiyat: {tech_data['price']}$, Değişim: %{tech_data['change_pct']}, RSI: {tech_data['rsi']}, Trend: {tech_data['trend']}
    
    SON HABERLER:
    {news_text}
    
    GÖREV: Haberleri ve teknik verileri harmanla. Puanlama yaparken CİMRİ ol. Her şeye yüksek puan verme.
    SADECE aşağıdaki JSON formatında yanıt ver:
    {{
        "karar": "GÜÇLÜ AL", "AL", "BEKLE", "SAT" veya "GÜÇLÜ SAT",
        "hedef_fiyat": (sayı),
        "stop_loss": (sayı),
        "kazanc_potansiyeli": (örn: "%12"),
        "risk_yuzdesi": (örn: "%-4"),
        "vade": (Tahmini elde tutma süresi, örn: "3-5 Gün", "2 Hafta"),
        "kasa_yonetimi": (Portföyün % kaçı, örn: "%5"),
        "guven_skoru": (0-100 arası sayı, 85 üstü çok nadir olsun),
        "analiz_ozeti": (Tek cümlelik net yorum)
    }}
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return None

# --- ANA MOTOR ---
def run_news_bot():
    print(f"[{datetime.now().strftime('%H:%M')}] 🧠 Haberler Toplanıyor...")
    
    # 1. ADIM: Haberleri Hisse Bazında Grupla
    stock_news_map = {} # { 'AAPL': ['Haber 1', 'Haber 2'], 'NVDA': ['Haber 1'] }
    stock_links_map = {}

    for url in RSS_URLS:
        d = feedparser.parse(url)
        for entry in d.entries[:5]: # Her kaynaktan son 5 haber
            title = entry.title
            for keyword, ticker in TRACKED_STOCKS.items():
                if keyword in title.lower():
                    if ticker not in stock_news_map:
                        stock_news_map[ticker] = []
                        stock_links_map[ticker] = entry.link
                    # Aynı haberi tekrar ekleme
                    if title not in stock_news_map[ticker]:
                        stock_news_map[ticker].append(title)
                    break
    
    print(f"📊 Toplam {len(stock_news_map)} farklı hisse için haber bulundu.")
    
    all_signals = []
    
    # 2. ADIM: Her Hisse İçin TEK Analiz Yap
    for ticker, news_list in stock_news_map.items():
        print(f"   🔍 Analiz: {ticker} ({len(news_list)} Haber)...")
        
        tech_data = get_technical_data(ticker)
        if not tech_data: continue
            
        ai_result = ask_gemini_consolidated(ticker, news_list, tech_data)
        
        if ai_result:
            signal = {
                "Tarih": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "Hisse": ticker,
                "Fiyat": tech_data['price'],
                "Karar": ai_result.get('karar', 'BEKLE'),
                "Hedef_Fiyat": ai_result.get('hedef_fiyat', 0),
                "Stop_Loss": ai_result.get('stop_loss', 0),
                "Kazanc_Potansiyeli": ai_result.get('kazanc_potansiyeli', '-'),
                "Risk_Yuzdesi": ai_result.get('risk_yuzdesi', '-'),
                "Vade": ai_result.get('vade', 'Belirsiz'),
                "Kasa_Yonetimi": ai_result.get('kasa_yonetimi', '-'),
                "Guven_Skoru": int(ai_result.get('guven_skoru', 0)),
                "Analiz_Ozeti": ai_result.get('analiz_ozeti', '-'),
                "Haber_Baslik": news_list[0], # İlk haberi referans alalım
                "Link": stock_links_map[ticker]
            }
            all_signals.append(signal)
            time.sleep(2)

    # 3. ADIM: Kaydet
    if all_signals:
        df = pd.DataFrame(all_signals)
        # Sütunları garantiye al
        cols = ["Tarih", "Hisse", "Karar", "Fiyat", "Hedef_Fiyat", "Stop_Loss", 
                "Guven_Skoru", "Vade", "Kasa_Yonetimi", "Kazanc_Potansiyeli", 
                "Risk_Yuzdesi", "Analiz_Ozeti", "Haber_Baslik", "Link"]
        
        # Dosya varsa oku, eski verilerle birleştir ama AYNI GÜNKÜ DUPLICATE'leri temizle
        if os.path.exists(OUTPUT_FILE):
            old_df = pd.read_csv(OUTPUT_FILE)
            combined_df = pd.concat([df, old_df])
            # Aynı hisse için en güncel analizi tut
            combined_df = combined_df.drop_duplicates(subset=['Hisse', 'Tarih'], keep='first')
            combined_df.to_csv(OUTPUT_FILE, index=False)
        else:
            df.to_csv(OUTPUT_FILE, index=False)
            
        print(f"✅ {len(all_signals)} analiz güncellendi.")
    else:
        print("💤 İşlenecek yeni veri yok.")

if __name__ == "__main__":
    run_news_bot()
