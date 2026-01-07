import os
import streamlit as st

# --- 1. VARSAYILAN DEĞERLER (ÇÖKMEYİ ÖNLEYEN SİGORTALAR) ---
# Eğer Secrets okunamazsa sistem patlamasın diye önce boş tanımlıyoruz.
GITHUB_TOKEN = ""
GIST_ID = ""
GEMINI_API_KEY = ""
RSS_URLS = []
WATCHLIST_TICKERS = []
TRACKED_STOCKS = []
OUTPUT_FILE = "sazlik_analiz_sonuclari.csv"

# --- 2. STREAMLIT SECRETS'TAN VERİ ÇEKME ---
try:
    # Streamlit ortamındaysak ve secrets varsa
    if hasattr(st, "secrets"):
        # Tek tek kontrol ederek çekiyoruz (KeyError hatasını önlemek için)
        if "GITHUB_TOKEN" in st.secrets:
            GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
            
        if "GIST_ID" in st.secrets:
            GIST_ID = st.secrets["GIST_ID"]
            
        if "GEMINI_API_KEY" in st.secrets:
            GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
            
        if "RSS_URLS" in st.secrets:
            RSS_URLS = st.secrets["RSS_URLS"]
            
        if "WATCHLIST_TICKERS" in st.secrets:
            WATCHLIST_TICKERS = st.secrets["WATCHLIST_TICKERS"]

except Exception as e:
    print(f"⚠️ Config Yükleme Hatası: {e}")

# --- 3. UYUMLULUK KÖPRÜSÜ ---
# Eski kodların çalışması için listeleri eşitliyoruz
if not TRACKED_STOCKS and WATCHLIST_TICKERS:
    TRACKED_STOCKS = WATCHLIST_TICKERS