import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import os

# --- AYARLAR ---
st.set_page_config(page_title="Sazlık AI", page_icon="🌾", layout="wide")

# API Anahtarını Secrets'tan al
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ API Anahtarı Bulunamadı! Lütfen Streamlit Secrets ayarlarını yapın.")
    st.stop()

# --- FONKSİYONLAR ---

def get_technical_status(ticker):
    try:
        symbol = f"{ticker}.IS" if not ticker.endswith(".IS") else ticker
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return None, "Veri Yok"
            
        price = hist['Close'].iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        
        # Basit Trend Analizi
        if price > sma20 * 1.02:
            trend = "GÜÇLÜ YÜKSELİŞ (Boğa) 🟢"
        elif price < sma20 * 0.98:
            trend = "DÜŞÜŞ TRENDİ (Ayı) 🔴"
        else:
            trend = "YATAY / KARARSIZ 🟡"
            
        return price, trend
    except Exception:
        return None, "Hata"

def ask_gemini(ticker, price, trend, news_text):
    """
    Hazırlanan promptu Google Gemini'ye gönderir ve cevabı alır.
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    SEN BİR PORTFÖY YÖNETİCİSİSİN.
    Aşağıdaki finansal verileri ve haberi analiz et.
    Duygusal olma, sadece matematiksel ve mantıksal konuş.

    1. VARLIK: {ticker}
    2. TEKNİK DURUM: Fiyat {price} TL. Ana Trend: {trend}
    3. HABER: "{news_text}"

    GÖREV:
    Bu haberin mevcut teknik trend üzerindeki etkisini yorumla.
    - Eğer trend kötüyse, bu haber trendi döndürebilir mi?
    - Eğer trend iyiyse, bu haber benzin olur mu yoksa "haber sat" fırsatı mı?

    ÇIKTI FORMATI:
    Kısa, net 3 madde halinde Türkçe yanıt ver.
    1. Etki Skoru (0-100)
    2. Kısa Yorum
    3. Swing Trade Önerisi (İzle / Alım Düşün / Uzak Dur)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Hatası: {str(e)}"

# --- ARAYÜZ (UI) ---

st.title("🌾 Sazlık: Bilimsel Haber Analizcisi")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Veri Girişi")
    ticker = st.text_input("Hisse Kodu (BIST)", "ASELS").upper()
    news = st.text_area("Haber Metni", height=150, placeholder="KAP haberini veya söylentiyi buraya yapıştır...")
    analyze_btn = st.button("Analiz Et 🚀", type="primary")

with col2:
    st.subheader("Analiz Sonuçları")
    
    if analyze_btn:
        if not ticker or not news:
            st.warning("Lütfen hisse kodu ve haber metni girin.")
        else:
            with st.spinner("Piyasa verileri taranıyor ve AI düşünüyor..."):
                # 1. Teknik Veri Çek
                price, trend = get_technical_status(ticker)
                
                if price:
                    # Metrikleri Göster
                    m1, m2 = st.columns(2)
                    m1.metric("Anlık Fiyat", f"{price:.2f} TL")
                    m2.metric("Teknik Trend", trend)
                    
                    st.divider()
                    
                    # 2. AI'a Sor
                    ai_result = ask_gemini(ticker, price, trend, news)
                    
                    # 3. Sonucu Yazdır
                    st.success("Analiz Tamamlandı!")
                    st.markdown(ai_result)
                else:
                    st.error("Hisse verisi çekilemedi. Kodu kontrol et.")

# Alt Bilgi
st.markdown("---")
st.caption("Bu sistem yatırım tavsiyesi vermez. Sazlık Projesi v0.2")

