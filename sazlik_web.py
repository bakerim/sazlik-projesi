import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import requests
import json

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık Pro: US Swing", page_icon="🇺🇸", layout="wide")

# --- API ANAHTARI ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ API Anahtarı yok! Secrets ayarlarını kontrol et.")
    st.stop()

# --- 1. MODÜL: ABD TEKNİK ANALİZİ ($) ---
def get_technical_status(ticker):
    try:
        # ABD Borsası için .IS EKLEMİYORUZ (Direkt AAPL, TSLA)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return None, "Veri Yok", 0
            
        price = hist['Close'].iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        
        # Volatilite Hesabı
        daily_change = (hist['High'] - hist['Low']).mean()
        volatility_pct = (daily_change / price) * 100
        
        # Trend
        if price > sma20 * 1.01:
            trend = "YÜKSELİŞ (Bullish) 🟢"
        elif price < sma20 * 0.99:
            trend = "DÜŞÜŞ (Bearish) 🔴"
        else:
            trend = "YATAY (Neutral) 🟡"
            
        return price, trend, volatility_pct
    except Exception as e:
        return None, f"Hata: {str(e)}", 0

# --- 2. MODÜL: OTOMATİK HAFIZA (Botun Topladığı Veriler) ---
def get_past_context(ticker):
    # Senin botunun doldurduğu gerçek dosya
    url = "https://raw.githubusercontent.com/bakerim/sazlik-projesi/main/news_archive.json"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return "⚠️ Bot dosyasına ulaşılamadı."
            
        data = response.json()
        
        # İlgili hissenin haberlerini süz
        found_news = []
        for item in data:
            if item.get('ticker') == ticker:
                # Tarih ve Başlık
                found_news.append(f"- [{item['date']}] {item['content']}")
        
        if found_news:
            # En güncel 5 haberi al
            return "\n".join(found_news[:5])
        else:
            return f"ℹ️ {ticker} için botun yakaladığı bir haber henüz yok."
    except:
        return "Veri okuma hatası."

# --- 3. MODÜL: HEDGE FUND AI (Gemini 2.0) ---
def ask_trader_ai(ticker, price, trend, volatility, context, news_text):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    SEN TECRÜBELİ BİR ABD BORSA TRADER'ISIN.
    
    ANALİZ VERİLERİ:
    1. HİSSE: {ticker} (Şu an: ${price:.2f})
    2. TREND: {trend}
    3. VOLATİLİTE: %{volatility:.2f}
    4. BOT İSTİHBARATI (Hafıza): 
    {context}
    
    5. ODAK HABER: 
    "{news_text}"

    GÖREV:
    Kısa vadeli (1-5 Gün) swing trade analizi yap.
    
    ÇIKTI FORMATI:
    ### 📊 TİCARET PLANI
    * **Karar:** (GÜÇLÜ AL / İZLE / SAT)
    * **Giriş:** ${price:.2f}
    * **Hedef (TP):** (Trende uygun hedef)
    * **Stop (SL):** (Mantıklı zarar kes)
    * **Vade:** (Gün sayısı)
    
    ### 🧠 ANALİZ
    (Kısa ve net yorum)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Hatası: {str(e)}"

# --- ARAYÜZ ---
st.title("🇺🇸 Sazlık Pro: Wall Street Edition")
st.caption("ABD Borsası Otomatik Analiz Sistemi")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("İşlem Masası")
    ticker = st.text_input("Sembol (Ticker)", "NVDA").upper()
    btn = st.button("Sinyal Üret ⚡", type="primary")

with col2:
    if btn:
        with st.spinner("Piyasa verileri taranıyor..."):
            # 1. Teknik
            price, trend, vol = get_technical_status(ticker)
            
            if price:
                c1, c2, c3 = st.columns(3)
                c1.metric("Fiyat", f"${price:.2f}")
                c2.metric("Trend", trend)
                c3.metric("Volatilite", f"%{vol:.2f}")
                
                # 2. Hafıza
                context = get_past_context(ticker)
                
                # Bot haber bulduysa onu kullan, bulamadıysa genel analiz yap
                main_news = "Genel teknik görünüm ve piyasa durumu analizi."
                if "haber henüz yok" not in context and "Hata" not in context:
                    main_news = context.split('\n')[0] # En güncel haberi al
                    st.info(f"📌 Analiz Edilen Haber: {main_news}")
                
                with st.expander("📂 Botun Topladığı Veriler"):
                    st.text(context)
                
                # 3. AI Kararı
                result = ask_trader_ai(ticker, price, trend, vol, context, main_news)
                
                st.markdown(result)
            else:
                st.error("Hisse bulunamadı. Lütfen 'NVDA', 'TSLA' gibi ABD kodları girin.")
