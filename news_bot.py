import feedparser
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
import os
import time
import json
import random
from datetime import datetime
from config import TRACKED_STOCKS, RSS_URLS, OUTPUT_FILE, WATCHLIST_TICKERS

# --- AYARLAR ---
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    print("⚠️ UYARI: GEMINI_API_KEY bulunamadı. Sadece Teknik Robot çalışacak.")

# --- GARANTİCİ BABA ALGORİTMASI (ROBOT) ---
def garantici_baba_analiz(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y") 
        if len(df) < 200: return None 
        
        current_price = df['Close'].iloc[-1]
        
        # İndikatörler
        df.ta.rsi(length=14, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)
        
        rsi = df['RSI_14'].iloc[-1]
        sma50 = df['SMA_50'].iloc[-1]
        sma200 = df['SMA_200'].iloc[-1]
        
        if pd.isna(rsi) or pd.isna(sma50): return None

        # Puanlama
        score = 50
        ozet_list = []
        vade_tahmini = "Belirsiz"
        
        # RSI ve Vade Mantığı
        if rsi < 30:
            score += 25
            ozet_list.append(f"RSI Dipte ({rsi:.0f})")
            vade_tahmini = "Kısa Vade (3-5 Gün)" # Tepki çabuk gelir
        elif rsi < 40:
            score += 10
            ozet_list.append("RSI Ucuz")
            vade_tahmini = "1-2 Hafta"
        elif rsi > 70:
            score -= 20
            ozet_list.append(f"RSI Tepede ({rsi:.0f})")
            vade_tahmini = "Gün İçi (Düzeltme)"
            
        # Trend
        if current_price > sma200:
            score += 15
            ozet_list.append("Trend Pozitif")
            if vade_tahmini == "Belirsiz": vade_tahmini = "Orta Vade (1 Ay+)"
        else:
            score -= 10
            ozet_list.append("Trend Negatif")
        
        # Karar
        karar = "BEKLE"
        if score >= 75: karar = "GÜÇLÜ AL"
        elif score >= 60: karar = "AL"
        elif score <= 30: karar = "SAT"
        
        return {
            "karar": karar,
            "guven_skoru": score,
            "analiz_ozeti": f"[GARANTİCİ BABA]: {' | '.join(ozet_list)}",
            "fiyat": round(current_price, 2),
            "rsi": round(rsi, 2),
            "hedef_fiyat": round(current_price * 1.05, 2),
            "stop_loss": round(current_price * 0.95, 2),
            "kazanc_pot": "%5",
            "risk_yuzde": "%-5",
            "vade": vade_tahmini # Artık dolu gelecek
        }
    except:
        return None

# --- GEMINI AI SORGUSU ---
def ask_gemini_consolidated(ticker, news_list, tech_data):
    if not API_KEY: return None
    
    news_text = "\n".join([f"- {n}" for n in news_list])
    prompt = f"""
    Sen Hedge Fon Yöneticisisin.
    HİSSE: {ticker}, FİYAT: {tech_data['price']}, RSI: {tech_data['rsi']}
    HABERLER: {news_text}
    
    GÖREV: VADE bilgisini mutlaka ver (örn: '1-3 Gün', '2 Hafta', '1 Ay'). Asla boş bırakma.
    
    JSON FORMATI:
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
    print(f"[{datetime.now().strftime('%H:%M')}] 🧠 Sazlık Hibrit Motoru (Vade Düzeltmeli)...")
    
    all_signals = []
    processed_tickers = set()
    
    # 1. AŞAMA: HABERLER
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
    except: pass

    for ticker, news_list in stock_news_map.items():
        print(f"   🤖 AI Analiz: {ticker}")
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
                "Vade": ai_result.get('vade', 'Belirsiz'), # AI'dan geleni al
                "Kasa_Yonetimi": ai_result.get('kasa_yonetimi', '-'),
                "Kazanc_Potansiyeli": ai_result.get('kazanc_potansiyeli', '-'),
                "Risk_Yuzdesi": ai_result.get('risk_yuzdesi', '-'),
                "Analiz_Ozeti": f"[AI]: {ai_result.get('analiz_ozeti', '-')}",
                "Haber_Baslik": news_list[0],
                "Link": stock_links_map[ticker]
            }
            all_signals.append(signal)
            processed_tickers.add(ticker)
            time.sleep(1)

    # 2. AŞAMA: ROBOT (RASTGELE 60 HİSSE)
    print("⚙️ Aşama 2: Garantici Baba Avda...")
    target_list = [t for t in WATCHLIST_TICKERS if t not in processed_tickers]
    scan_list = random.sample(target_list, min(len(target_list), 60))

    for ticker in scan_list:
        try:
            res = garantici_baba_analiz(ticker)
            # FİLTRE: 60 Üstü veya 30 Altı
            if res and (res['guven_skoru'] >= 60 or res['guven_skoru'] <= 30):
                print(f"   ✅ FIRSAT: {ticker} ({res['vade']})")
                signal = {
                    "Tarih": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "Hisse": ticker,
                    "Fiyat": res['fiyat'],
                    "Karar": res['karar'],
                    "Hedef_Fiyat": res['hedef_fiyat'],
                    "Stop_Loss": res['stop_loss'],
                    "Guven_Skoru": res['guven_skoru'],
                    "Vade": res['vade'], # Robotun ürettiği vade
                    "Kasa_Yonetimi": "%5 (Robot)",
                    "Kazanc_Potansiyeli": res['kazanc_pot'],
                    "Risk_Yuzdesi": res['risk_yuzde'],
                    "Analiz_Ozeti": res['analiz_ozeti'],
                    "Haber_Baslik": "Teknik Tarama (Haber Yok)",
                    "Link": f"https://finance.yahoo.com/quote/{ticker}"
                }
                all_signals.append(signal)
        except: continue

    # KAYDET
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
            except: df.to_csv(OUTPUT_FILE, index=False)
        else:
            df.to_csv(OUTPUT_FILE, index=False)
        print(f"✅ {len(all_signals)} analiz kaydedildi.")
    else:
        print("💤 Veri yok.")

if __name__ == "__main__":
    run_news_bot()
