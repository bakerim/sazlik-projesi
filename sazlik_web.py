import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık AI 2.0", page_icon="🌾", layout="wide")

# --- API ANAHTARI KONTROLÜ ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ API Anahtarı Bulunamadı! Streamlit Secrets ayarlarını kontrol et.")
    st.stop()

# --- 1. MODÜL: TEKNİK ANALİZ (GÖZ) ---
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
        if price > sma20 * 1.01:
            trend = "YÜKSELİŞ TRENDİ (Boğa) 🟢"
        elif price < sma20 * 0.99:
            trend = "DÜŞÜŞ TRENDİ (Ayı) 🔴"
        else:
            trend = "YATAY / KARARSIZ 🟡"
            
        return price, trend
    except Exception as e:
        return None, "Hata"

# --- 2. MODÜL: HAFIZA / RAG (DEMO) ---
def get_past_context(ticker):
    """
    Normalde burası veritabanından çeker.
    Şimdilik TKFEN örneği için hafızayı simüle ediyoruz.
    """
    if ticker == "TKFEN":
        return """
        ⚠️ SİSTEM HAFIZASI (Son 30 Gün):
        - [2024-12-01] Katar'da 200 Milyon Dolarlık ihale süreci başladı. (Olumlu)
        - [2024-11-20] Şirket bilançosu beklenti altı geldi. (Olumsuz)
        - [2024-11-15] CEO değişikliği haberi düştü. (Nötr)
        """
    elif ticker == "ASELS":
        return """
        ⚠️ SİSTEM HAFIZASI (Son 30 Gün):
        - [2024-12-03] Yeni ihracat sözleşmesi imzalandı. (Olumlu)
        - [2024-11-28] Savunma sanayi hisselerinde genel satış baskısı var. (Sektörel)
        """
    else:
        return "ℹ️ Bu hisse için arşivde kayıtlı geçmiş kritik bir haber bulunamadı."

# --- 3. MODÜL: AI BEYNİ (GEMINI 2.0) ---
def ask_gemini(ticker, price, trend, context, news_text):
    # EN GÜNCEL MODEL
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    SEN UZMAN BİR SWING TRADE ALGORİTMASISIN.
    Aşağıdaki verileri birleştir ve karar ver.

    1. HİSSE: {ticker}
    2. CANLI TEKNİK: Fiyat {price:.2f} TL | Durum: {trend}
    3. GEÇMİŞ BAĞLAM (HAFIZA): 
    {context}
    
    4. YENİ GELEN HABER: 
    "{news_text}"

    GÖREV:
    Bu haberin, MEVCUT TREND ve GEÇMİŞ BAĞLAM ışığında fiyata etkisini analiz et.
    Hafızadaki bilgilerle yeni haberi çelişiyor mu yoksa destekliyor mu kontrol et.

    ÇIKTI FORMATI (Türkçe):
    1. Etki Skoru: (0-100 arası puan)
    2. Analiz: (Kısa, net, finansal dilde yorum)
    3. Swing Sinyali: (Güçlü Al / Kademeli Al / İzle / Sat / Uzak Dur)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Bağlantı Hatası: {str(e)}"

# --- ARAYÜZ (UI) ---
st.title("🌾 Sazlık Projesi v2.0")
st.caption("Powered by Gemini 2.0 Flash & GitHub RAG Architecture")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Sinyal Paneli")
    ticker = st.text_input("Hisse Kodu", "TKFEN").upper()
    news = st.text_area("Haber / Duyum", height=150, placeholder="Haberi buraya yapıştır...")
    analyze_btn = st.button("Analiz Et (Gemini 2.0)", type="primary")

with col2:
    if analyze_btn and ticker and news:
        with st.spinner("Piyasa verileri ve arşiv taranıyor..."):
            # 1. Teknik Veri
            price, trend = get_technical_status(ticker)
            
            if price:
                # Metrik Gösterimi
                m1, m2 = st.columns(2)
                m1.metric("Fiyat", f"{price:.2f} TL")
                m2.metric("Trend", trend)
                
                # 2. Hafıza (RAG)
                context = get_past_context(ticker)
                with st.expander("📂 Sazlık Hafızası (Geçmiş Veriler)"):
                    st.info(context)
                
                # 3. AI Analizi
                result = ask_gemini(ticker, price, trend, context, news)
                
                st.markdown("### 🤖 Yapay Zeka Kararı")
                st.success("Analiz Tamamlandı")
                st.markdown(result)
            else:
                st.error("Hisse bulunamadı. Kodu kontrol et (Örn: THYAO).")

# Alt Bilgi
st.markdown("---")
st.info("Not: Bu sistem demo amaçlıdır. Yatırım tavsiyesi içermez.")
