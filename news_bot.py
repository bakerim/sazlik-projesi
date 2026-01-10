import yfinance as yf
import pandas as pd
from google import genai
import ta 
import time 
import config 
import json

# --- YENİ NESİL MOTOR ---
try:
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    MODEL_NAME = 'gemini-3-flash-preview' 
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False

def get_technical_analysis(ticker):
    """ V7.0 GADDAR ANALİZ """
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
            "Pot_Kar": (( (curr + (atr * 3.0)) - curr) / curr) * 100,
            "Summary": f"Fiyat: {curr:.2f}, RSI: {rsi:.1f}, ATR Bazlı Volatilite yüksek."
        }
        return score, curr, data
    except: return 0, 0, None

def run_analysis_engine():
    all_tech_results = []
    total = len(config.WATCHLIST_TICKERS)
    print(f"📡 {total} hisse taranıyor...")
    
    # 1. ADIM: TEKNİK ÖN ELEME
    for index, symbol in enumerate(config.WATCHLIST_TICKERS):
        print(f"🔍 [{index+1}/{total}] {symbol}", end="\r")
        base_score, price, data = get_technical_analysis(symbol)
        if base_score >= 55:
            all_tech_results.append({
                "symbol": symbol, "price": price, "base_score": base_score, "data": data
            })
    
    # 2. ADIM: EN İYİ 6 ADAYI SEÇ
    finalists = sorted(all_tech_results, key=lambda x: x['base_score'], reverse=True)[:6]
    
    if not finalists: return []

    # 3. ADIM: TEK BİR PROMPT İLE TOPLU HABER VE AI ANALİZİ
    print(f"\n🧠 Gemini 3 ({MODEL_NAME}) Toplu Analiz Başlatıyor...")
    
    # Finalistleri metin haline getir
    candidates_text = "\n".join([f"- {c['symbol']}: {c['data']['Summary']}" for c in finalists])
    
    prompt = f"""
    Aşağıdaki 6 hisse için güncel haberleri ve piyasa duyarlılığını (Sentiment) analiz et. 
    Her hisse için 0-10 arası bir EK PUAN ver ve kısa bir yorum yap. 
    Hisseler:
    {candidates_text}

    Yanıtı şu JSON formatında ver:
    {{"HisseSembolü": {{"ek_puan": 5.5, "yorum": "Haberler pozitif, direnç kırıldı."}}}}
    """

    final_results = []
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        # JSON temizleme (Markdown bloklarını kaldır)
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        ai_data = json.loads(raw_text)
        
        for c in finalists:
            symbol = c['symbol']
            res = ai_data.get(symbol, {"ek_puan": 5.0, "yorum": "Analiz hazır."})
            
            final_score = min(100.0, c['base_score'] + float(res['ek_puan']))
            final_results.append({
                "Hisse": symbol, "Fiyat": c['price'], "Guven_Skoru": final_score,
                "AI_Notu": res['yorum'], "Stop": c['data']['Stop'], 
                "Hedef": c['data']['Hedef'], "Pot_Kar": c['data']['Pot_Kar']
            })
    except Exception as e:
        print(f"⚠️ Toplu Analiz Hatası: {e}")
        # Hata olursa teknik verilerle devam et
        for c in finalists:
            final_results.append({
                "Hisse": c['symbol'], "Fiyat": c['price'], "Guven_Skoru": c['base_score'],
                "AI_Notu": "Teknik analiz bazlı rapor.", "Stop": c['data']['Stop'], 
                "Hedef": c['data']['Hedef'], "Pot_Kar": c['data']['Pot_Kar']
            })

    return sorted(final_results, key=lambda x: x['Guven_Skoru'], reverse=True)