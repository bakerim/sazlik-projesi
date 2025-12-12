import feedparser
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
import os
import time
import json
import random # Rastgelelik için eklendi
from datetime import datetime
from config import TRACKED_STOCKS, RSS_URLS, OUTPUT_FILE, WATCHLIST_TICKERS

# --- AYARLAR ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# API Key kontrolü (Yoksa sadece Robot çalışsın diye hata vermiyoruz, uyarıyoruz)
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    print("⚠️ UYARI: GEMINI_API_KEY bulunamadı. Sadece Teknik Robot çalışacak.")

# --- GARANTİCİ BABA ALGORİTMASI (ROBOT) ---
def garantici_baba_analiz(ticker):
    """
    Haberden bağımsız, tamamen teknik verilere dayalı puanlama yapar.
    """
    try:
        stock = yf.Ticker(ticker)
        # Veri çekme (Daha hızlı olması için periodu optimize ettik)
        df = stock.history(period="1y") 
        if len(df) < 200: return None 
        
        current_price = df['Close'].iloc[-1]
        
        # --- TEKNİK İNDİKATÖRLER ---
        df.ta.rsi(length=14, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)
        
        # Son değerler
        rsi = df['RSI_14'].iloc[-1]
        sma50 = df['SMA_50'].iloc[-1]
        sma200 = df['SMA_200'].iloc[-1]
        
        # NaN kontrolü
        if pd.isna(rsi) or pd.isna(sma50) or pd.isna(sma200): return None

        # --- PUANLAMA MANTIĞI (0-100) ---
        score = 50 # Nötr
        ozet_list = []
        
        # 1. RSI (Tepki Alımı Fırsatı)
        if rsi < 30:
            score += 25
            ozet_list.append(f"RSI Dipte ({rsi:.0f})")
        elif rsi < 40:
            score += 10
            ozet_list.append("RSI Ucuz")
        elif rsi > 70:
            score -= 20
            ozet_list.append(f"RSI Tepede ({rsi:.0f})")
            
        # 2. TREND (SMA 200)
        if current_price > sma200:
            score += 15
            ozet_list.append("Trend Pozitif")
        else:
            score -= 10
            ozet_list.append("Trend Negatif")
            
        # 3. GOLDEN CROSS
        if sma50 > sma200:
            score += 10
        
        # 4. FİYAT KONUMU
        if current_price > sma50:
            score += 5
        
        # --- KARAR ---
        karar = "BEKLE"
        if score >= 75: karar = "GÜÇLÜ AL"
        elif score >= 60: karar = "AL" # Eşik 65'ten 60'a indi
        elif score <= 30: karar = "SAT"
        
        # Robot Raporu
        analiz_metni = " | ".join(ozet_list)
        analiz_metni = f"[GARANTİCİ BABA]: {analiz_metni}"
        
        return {
            "karar": karar,
            "guven_skoru": score,
            "analiz_ozeti": analiz_metni,
            "fiyat": round(current_price, 2),
            "rsi": round(rsi, 2),
            "hedef_fiyat": round(current_price * 1.05, 2),
            "stop_loss": round(current_price * 0.95, 2),
            "kazanc_pot": "%5 (Teknik)",
            "risk_yuzde": "%-5 (Teknik)",
            "vade": "Teknik Tepki"
        }
        
    except Exception as e:
        return None

# --- GEMINI AI SORGUSU ---
def ask_gemini_consolidated(ticker, news_list, tech_data):
    if not API_KEY: return None
    
    news_text = "\n".join([f"- {n}" for n in news_list])
    prompt = f"""
    Sen acımasız bir Hedge Fon Yöneticisisin.
    HİSSE: {ticker}, FİYAT: {tech_data['price']}, RSI: {tech_data['rsi']}
    HABERLER: {news_text}
    SADECE JSON VER:
    {{
        "karar": "AL/SAT/BEKLE", "hedef_fiyat": sayı, "stop_loss": sayı,
        "kazanc_potansiyeli": "yüzde", "risk_yuzdesi": "yüzde",
        "vade": "süre", "kasa_yonetimi": "yüzde", "guven_skoru": sayı,
        "analiz_ozeti": "kısa yorum"
    }}
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return None

# --- ANA MOTOR ---
def run_news_bot():
    print(f"[{datetime.now().strftime('%H:%M')}] 🧠 Sazlık Hibrit Motoru Başlatılıyor...")
    
    all_signals = []
    processed_tickers = set()
    
    # ---------------------------------------------------------
    # 1. AŞAMA: SICAK FIRSATLAR (HABER)
    # ---------------------------------------------------------
    print("📡 Aşama 1: Haberler Taranıyor...")
    stock_news_map = {}
    stock_links_map = {}

    try:
        for url in RSS_URLS:
            d = feedparser.parse(url)
            for entry in d.entries[:5]:
                title = entry.title
                for keyword, ticker in TRACKED_STOCKS.items():
                    if keyword in title.lower():
                        if ticker not in stock_news_map:
                            stock_news_map[ticker] = []
                            stock_links_map[ticker] = entry.link
                        if title not in stock_news_map[ticker]:
                            stock_news_map[ticker].append(title)
                        break
    except Exception as e:
        print(f"RSS Hatası: {e}")

    for ticker, news_list in stock_news_map.items():
        print(f"   🤖 AI Analiz: {ticker}")
        
        # Robot verisini al (Teknik destek için)
        robot_data = garantici_baba_analiz(ticker)
        if not robot_data: continue
            
        ai_result = ask_gemini_consolidated(ticker, news_list, {"price": robot_data['fiyat'], "rsi": robot_data['rsi']})
        
        if ai_result:
            signal = {
                "Tarih": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "Hisse": ticker,
                "Fiyat": robot_data['fiyat'],
                "Karar": ai_result.get('karar', 'BEKLE'),
                "Hedef_Fiyat": ai_result.get('hedef_fiyat', 0),
                "Stop_Loss": ai_result.get('stop_loss', 0),
                "Guven_Skoru": int(ai_result.get('guven_skoru', 0)),
                "Vade": ai_result.get('vade', '-'),
                "Kasa_Yonetimi": ai_result.get('kasa_yonetimi', '-'),
                "Kazanc_Potansiyeli": ai_result.get('kazanc_potansiyeli', '-'),
                "Risk_Yuzdesi": ai_result.get('risk_yuzdesi', '-'),
                "Analiz_Ozeti": f"[AI]: {ai_result.get('analiz_ozeti', '-')}",
                "Haber_Baslik": news_list[0],
                "Link": stock_links_map[ticker]
            }
            all_signals.append(signal)
            processed_tickers.add(ticker)
            time.sleep(1) # API nezaketi

    # ---------------------------------------------------------
    # 2. AŞAMA: GARANTİCİ BABA (RASTGELE AVCI MODU)
    # ---------------------------------------------------------
    print("⚙️ Aşama 2: Garantici Baba Avda...")
    
    # LİSTEYİ KARIŞTIR (Her seferinde farklı hisseleri tara)
    # 50 tane rastgele hisse seçelim. Bu işlem süresini kısaltır ve çeşitlilik sağlar.
    target_list = [t for t in WATCHLIST_TICKERS if t not in processed_tickers]
    scan_list = random.sample(target_list, min(len(target_list), 60)) # 60 Hisse Tara
    
    print(f"   🎲 {len(scan_list)} rastgele hisse seçildi ve taranıyor...")

    for ticker in scan_list:
        try:
            res = garantici_baba_analiz(ticker)
            
            # FİLTRE: Sadece Kayda Değer Olanları Al (60 üstü veya 30 altı)
            if res and (res['guven_skoru'] >= 60 or res['guven_skoru'] <= 30):
                print(f"   ✅ FIRSAT BULUNDU: {ticker} (Skor: {res['guven_skoru']})")
                
                signal = {
                    "Tarih": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "Hisse": ticker,
                    "Fiyat": res['fiyat'],
                    "Karar": res['karar'],
                    "Hedef_Fiyat": res['hedef_fiyat'],
                    "Stop_Loss": res['stop_loss'],
                    "Guven_Skoru": res['guven_skoru'],
                    "Vade": res['vade'],
                    "Kasa_Yonetimi": "%5 (Robot)",
                    "Kazanc_Potansiyeli": res['kazanc_pot'],
                    "Risk_Yuzdesi": res['risk_yuzde'],
                    "Analiz_Ozeti": res['analiz_ozeti'],
                    "Haber_Baslik": "Teknik Tarama (Haber Yok)",
                    "Link": f"https://finance.yahoo.com/quote/{ticker}"
                }
                all_signals.append(signal)
                
        except Exception as e:
            continue

    # ---------------------------------------------------------
    # KAYDET
    # ---------------------------------------------------------
    if all_signals:
        df = pd.DataFrame(all_signals)
        cols = ["Tarih", "Hisse", "Karar", "Fiyat", "Hedef_Fiyat", "Stop_Loss", 
                "Guven_Skoru", "Vade", "Kasa_Yonetimi", "Kazanc_Potansiyeli", 
                "Risk_Yuzdesi", "Analiz_Ozeti", "Haber_Baslik", "Link"]
        
        for c in cols:
            if c not in df.columns: df[c] = "-"
        df = df[cols]

        if os.path.exists(OUTPUT_FILE):
            try:
                old_df = pd.read_csv(OUTPUT_FILE)
                combined_df = pd.concat([df, old_df])
                combined_df = combined_df.drop_duplicates(subset=['Hisse'], keep='first')
                combined_df.to_csv(OUTPUT_FILE, index=False)
            except:
                df.to_csv(OUTPUT_FILE, index=False)
        else:
            df.to_csv(OUTPUT_FILE, index=False)
            
        print(f"✅ Toplam {len(all_signals)} analiz kaydedildi.")
    else:
        print("💤 Piyasalar çok sessiz, kayda değer bir şey çıkmadı.")

if __name__ == "__main__":
    run_news_bot()
