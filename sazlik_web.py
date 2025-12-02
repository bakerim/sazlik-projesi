import streamlit as st
import google.generativeai as genai
import feedparser
import json
import time
import yfinance as yf

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık: SwingSniper", page_icon="🎯", layout="wide")

# --- 2. CSS TASARIM ---
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .signal-card {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid;
        background-color: #1c1c1c; /* Kart arka planı */
    }
    .success { border-color: #00ff00; } /* Yeşil */
    .warning { border-color: #ffaa00; } /* Turuncu/Sarı */
    .danger { border-color: #ff0000; }  /* Kırmızı (Hata durumunda) */
</style>
""", unsafe_allow_html=True)

# --- 3. AKILLI FİYAT FONKSİYONU (GAP VE TİCKER DÜZELTME) ---
def get_price_data(ticker):
    """
    1. Önce verilen Ticker'ı dener.
    2. Olmazsa sonuna .IS ekleyip dener (BIST hisseleri için).
    3. Dünkü kapanışa göre % değişimi hesaplar (Gap-Up tuzağına düşmemek için).
    """
    found_ticker = ticker # Hangi isimle bulduğumuzu takip edelim
    
    try:
        # 1. Deneme: Saf Ticker (Örn: FBYD)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        # 2. Deneme: Eğer veri yoksa ve kısa bir kodsa, BIST olabilir (.IS ekle)
        if hist.empty:
            found_ticker = f"{ticker}.IS"
            stock = yf.Ticker(found_ticker)
            hist = stock.history(period="5d")

        # Veri geldi mi kontrol et
        if not hist.empty and len(hist) >= 2:
            current_price = hist['Close'].iloc[-1]   # Anlık Fiyat
            prev_close = hist['Close'].iloc[-2]      # Dünkü Kapanış (Referans)
            
            # Gerçek Yüzdelik Değişim Hesapla
            change_percent = ((current_price - prev_close) / prev_close) * 100
            return change_percent, current_price, found_ticker
        else:
            return None, None, None
            
    except Exception as e:
        return None, None, None

# --- 4. KENAR ÇUBUĞU ---
with st.sidebar:
    st.title("🎛️ Kontrol Paneli")
    st.write("Sazlık Projesi - Web v3.2")
    api_key = st.text_input("Google Gemini API Key", type="password")
    st.divider()
    st.info("💡 **Garantici Mod Açık:**\nSistem; global riskleri, ticker hatalarını ve anlık fiyat şişkinliğini kontrol eder.")

# --- 5. ANA EKRAN ---
st.title("🎯 SwingSniper: Sazlık Projesi")
st.markdown("**Durum:** `Sistem Aktif` | **Mod:** `Defansif / Aile Babası` | **Versiyon:** `v3.2 (Smart Price)`")

# --- 6. PROMPT (YAPAY ZEKA TALİMATI) ---
SYSTEM_PROMPT = """
**ROLE:**
Sen "Sazlık Projesi"nin Baş Stratejistisin. Kimliğin: Aşırı şüpheci, garantici ve defansif bir Swing Trader. 
Kullanıcın (Mert),
