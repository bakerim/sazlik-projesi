import yfinance as yf
import pandas as pd
from google import genai
import ta 
import time 
import config 
import json

# --- YENİ NESİL MOTOR KURULUMU ---
try:
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    MODEL_NAME = 'gemini-3-flash-preview' 
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False

def get_technical_analysis(ticker):
    """ V7.0 GADDAR ANALİZ - 79 PUAN BARAJI İÇİN """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty or len(df) < 200: return 0, 0, None

        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)

        curr = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        sma200 = df['SMA_200'].iloc[-1]
        sma50 = df['SMA_50'].iloc[-1]
        atr = df['ATR'].iloc[-1]

        # GADDAR FİLTRE: SMA 200 Altı Elenir
        if curr < sma200: return 0, curr, None 

        score = 50.0 
        if rsi < 30: score += 30.0    
        elif rsi < 40: score += 20.0  
        elif rsi < 50: score += 10.0  
        
        if curr > sma50: score += 10.0
        score += (50 - rsi) / 10.0 

        data = {
            "Stop": curr - (atr * 2.0),
            "Hedef": curr + (atr * 3.0),
            "Pot_Kar": (((curr + (atr * 3.0)) - curr) / curr) * 100,
            "Summary": f"Fiyat: {curr:.2f}, RSI: {rsi:.1f}, ATR Bazlı volatilite verisi."
        }
        return score, curr, data
    except: return 0, 0, None

def run_analysis_engine():
    all_tech_results = []
    # Yahoo'yu bozan kelimeler
    blacklist = ["PORTFOY", "CEZALAR", "KASA", "NAKIT", "TOPLAM", "YATIRIM"]
    clean_tickers = [t for t in config.WATCHLIST_TICKERS if t not in blacklist]
    
    total = len(clean_tickers)
    print(f"📡 {total} gerçek hisse taranıyor (Baraj: 79 Puan)...")
    
    # 1. ADIM: TEKNİK ÖN ELEME (Bedava)
    for index, symbol in enumerate(clean_tickers):
        print(f"🔍 [{index+1}/{total}] {symbol}", end="\r")
        base_score, price, data = get_technical_analysis(symbol)
        
        # KESİN KURAL: Sadece 79+ puanlılar Gemini'ye gidebilir
        if base_score >= 79:
            all_tech_results.append({
                "symbol": symbol, "price": price, "base_score": base_score, "data": data
            })
    
    if not all_tech_results:
        print("\n⚠️ 79 puan barajını geçen elit hisse bulunamadı.")
        return []

    # En iyi 6 adayı seç
    finalists = sorted(all_tech_results, key=lambda x: x['base_score'], reverse=True)[:6]
    
    # 2. ADIM: TOPLU GEMINI 3 ANALİZİ (Haber & Sentiment)
    print(f"\n🧠 Gemini 3 ({MODEL_NAME}) Toplu Analiz Başlatıyor...")
    
    candidates_info = "\n".join([f"- {c['symbol']}: {c['data']['Summary']}" for c in finalists])
    
    prompt = f"""
    Aşağıdaki 6 hisse için 2026 güncel haberlerini ve piyasa duyarlılığını analiz et. 
    Her biri için 0-10 arası EK PUAN ver ve kısa Türkçe yorum yap. 
    Hisseler:
    {candidates_info}

    Yanıtı SADECE şu JSON formatında ver (başka yazı ekleme):
    {{"HisseSembolü": {{"ek_puan": 5.5, "yorum": "Haber akışı güçlü."}}}}
    """

    final_results = []
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        ai_data = json.loads(raw_text)
        
        for c in finalists:
            symbol = c['symbol']
            res = ai_data.get(symbol, {"ek_puan": 5.0, "yorum": "Analiz tamamlandı."})
            
            final_score = min(100.0, c['base_score'] + float(res['ek_puan']))
            final_results.append({
                "Hisse": symbol, "Fiyat": c['price'], "Guven_Skoru": final_score,
                "AI_Notu": res['yorum'], "Stop": c['data']['Stop'], 
                "Hedef": c['data']['Hedef'], "Pot_Kar": c['data']['Pot_Kar']
            })
    except Exception as e:
        print(f"⚠️ Toplu Analiz Hatası: {e}")
        for c in finalists:
            final_results.append({
                "Hisse": c['symbol'], "Fiyat": c['price'], "Guven_Skoru": c['base_score'],
                "AI_Notu": "Haber taraması atlandı, teknik veri esas.", "Stop": c['data']['Stop'], 
                "Hedef": c['data']['Hedef'], "Pot_Kar": c['data']['Pot_Kar']
            })

    return sorted(final_results, key=lambda x: x['Guven_Skoru'], reverse=True)