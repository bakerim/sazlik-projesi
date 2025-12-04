import streamlit as st
import pandas as pd
import yfinance as yf
import os
from datetime import datetime, timedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık AI", page_icon="🌾")

st.title("🌾 Sazlık Projesi: AI Destekli Swing Sinyal")
st.markdown("Bilimsel veri analizi ve RAG mimarisi testi.")

# --- FONKSİYONLAR ---

def get_technical_status(ticker):
    try:
        symbol = f"{ticker}.IS" if not ticker.endswith(".IS") else ticker
        stock = yf.Ticker(symbol)
        
        # Son 1 aylık veri
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return None, "Veri Yok"
            
        price = hist['Close'].iloc[-1]
        
        # Basit Trend
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        trend = "YÜKSELİŞ 🟢" if price > sma20 else "DÜŞÜŞ 🔴"
        
        return price, trend
    except Exception as e:
        return None, f"Hata: {str(e)}"

def get_past_context(ticker):
    # Şimdilik demo amaçlı statik bir veri döndürelim
    # Dosya okuma işini sonra ekleriz, önce ekranda yazı görelim.
    return f"{ticker} için son 30 günde önemli bir KAP haberi bulunmadı."

def generate_prompt(ticker, price, trend, news_content):
    return f"""
    ANALİZ EDİLECEK HİSSE: {ticker}
    FİYAT: {price} TL
    TREND: {trend}
    HABER: {news_content}
    
    GÖREV: Bu verilerle swing trade analizi yap.
    """

# --- ARAYÜZ (UI) ---

# Kullanıcıdan Veri Alma
ticker_input = st.text_input("Hisse Kodu Girin (Örn: ASELS, THYAO)", "ASELS")
news_input = st.text_area("Haber Metnini Girin:", "Şirket yeni bir iş anlaşması imzaladı.")

if st.button("Analiz Et (Bilimsel Yaklaşım)"):
    
    if not ticker_input:
        st.warning("Lütfen bir hisse kodu girin.")
    else:
        # 1. Adım: Yükleniyor animasyonu
        with st.spinner(f'{ticker_input} için veriler toplanıyor...'):
            
            # 2. Adım: Teknik Verileri Çek
            price, trend = get_technical_status(ticker_input)
            
            if price is None:
                st.error(f"Teknik veri alınamadı: {trend}")
            else:
                # 3. Adım: Sonuçları Ekrana Bas (Print yerine st.metric kullanıyoruz)
                col1, col2 = st.columns(2)
                col1.metric("Anlık Fiyat", f"{price:.2f} TL")
                col2.metric("Ana Trend", trend)
                
                # 4. Adım: RAG/Bağlam Bilgisi
                context = get_past_context(ticker_input)
                with st.expander("Geçmiş Bağlam (Hafıza)"):
                    st.info(context)
                
                # 5. Adım: Prompt Oluşturma
                final_prompt = generate_prompt(ticker_input, price, trend, news_input)
                
                st.subheader("AI'a Gönderilecek Prompt:")
                st.code(final_prompt, language='text')
                
                st.success("Sistem başarıyla çalıştı! Şu an AI entegrasyonu beklemede.")

# Yan menü (Sidebar)
with st.sidebar:
    st.header("Sazlık v0.1")
    st.write("Bu proje RAG mimarisi kullanmaktadır.")
    if st.button("Önbelleği Temizle"):
        st.cache_data.clear()
