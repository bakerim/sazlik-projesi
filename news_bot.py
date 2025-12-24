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
    print("⚠️ UYARI: GEMINI_API_KEY bulunamadı.")

# --- GELİŞMİŞ GARANTİCİ BABA ALGORİTMASI ---

def garantici_baba_analiz(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Son 3 ay yeterli, bize hız lazım
        df = stock.history(period="3mo") 
        if len(df) < 50: return None 
        
        current_price = df['Close'].iloc[-1]
        
        # --- İNDİKATÖRLER VE HIZ HESABI ---
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=20, append=True)
        # ATR (Hissenin günlük hareket marjı - HIZ GÖSTERGESİ)
        df.ta.atr(length=14, append=True)
        
        rsi = df['RSI_14'].iloc[-1]
        ema20 = df['EMA_20'].iloc[-1]
        atr = df['ATRr_14'].iloc[-1]
        
        if pd.isna(rsi) or pd.isna(atr): return None

        # HIZ HESABI (Yüzde olarak günde ne kadar oynuyor?)
        hiz_yuzdesi = (atr / current_price) * 100
        
        # SÜZGEÇ 1: Çok yavaşsa (günde %1.5 altı) bize gelmesin, zaman kaybı.
        if hiz_yuzdesi < 1.5: return None

        # --- PUANLAMA (VUR-KAÇ ODAKLI) ---
        score = 50
        sebepler = []
        
        # 1. Trend (EMA20 üstündeyse yukarı gidiyordur)
        if current_price > ema20:
            score += 30
            sebepler.append("Trend Yukarı")
        
        # 2. Momentum (RSI 50-65 arası en tatlı, en hızlı yerdir)
        if 50 <= rsi <= 65:
            score += 30
            sebepler.append("RSI Patlamaya Hazır")
        elif rsi < 30: # Dip tepkisi
            score += 20
            sebepler.append("Dip Tepkisi")
        elif rsi > 70: # Çok şişmiş
            score -= 10
            sebepler.append("Aşırı Şişik")

        # 3. Hız Puanı
        if hiz_yuzdesi > 3.0:
            score += 20
            sebepler.append("Çok Hızlı")
        
        # --- SÜRE HESABI (MATEMATİKSEL) ---
        # Hedefimiz %5. Hisse günde %2.5 gidiyorsa, hedef 2 günde gelir.
        tahmini_gun = max(1, int(5 / hiz_yuzdesi))
        vade_str = f"1-{tahmini_gun + 1} Gün" # +1 gün opsiyon

        # Karar Mekanizması
        karar = "BEKLE"
        if score >= 80: karar = "GÜÇLÜ AL"
        elif score >= 60: karar = "AL"
        
        analiz_metni = " | ".join(sebepler)
        
        return {
            "karar": karar,
            "guven_skoru": score,
            "analiz_ozeti": analiz_metni,
            "fiyat": round(current_price, 2),
            "rsi": round(rsi, 2),
            # HEDEFİMİZ FIX %5
            "hedef_fiyat": round(current_price * 1.05, 2), 
            "stop_loss": round(current_price * 0.96, 2), # Stop %4
            "kazanc_pot": "%5",
            "vade": vade_str, # Artık "1-2 Hafta" yok, "1-3 Gün" var.
            "hiz": round(hiz_yuzdesi, 2)
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
    
    GÖREV: VADE bilgisini (örn: '1-3 Gün', '2 Hafta') ve KAZANC_POTANSIYELI (örn: '%12') mutlaka ver.
    
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
    print(f"[{datetime.now().strftime('%H:%M')}] 🧠 Sazlık Hibrit Motoru Başlatılıyor...")
    
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
                "Vade": ai_result.get('vade', 'Belirsiz'),
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
                    "Vade": res['vade'],
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
