import streamlit as st
import google.generativeai as genai
import feedparser
import json
import time
import yfinance as yf

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık: SwingSniper", page_icon="🎯", layout="wide")

# --- CSS İLE GÖRSELİ GÜZELLEŞTİRME ---
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .big-font {
        font-size:20px !important;
        color: #e0e0e0;
    }
    .signal-card {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid;
    }
    .success { background-color: #1e3a2f; border-color: #00ff00; }
    .warning { background-color: #3a2e1e; border-color: #ffaa00; }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYON: FİYAT KONTROLÜ ---
def get_price_data(ticker):
    """
    Hissenin anlık fiyat değişimini kontrol eder.
    Eğer hisse çoktan uçmuşsa bizi uyarır.
    """
    try:
        # BIST hissesi mi Global mi anlamaya çalışalım
        # BIST ise sonuna .IS eklemek gerekebilir (Örn: THYAO -> THYAO.IS)
        # Önce olduğu gibi deneyelim
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        
        # Eğer boş gelirse ve 5 harfliden azsa (TR hissesi gibi) sonuna .IS ekleyelim
        if hist.empty:
            stock = yf.Ticker(f"{ticker}.IS")
            hist = stock.history(period="1d")

        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[0]
            # Yüzdelik değişimi hesapla
            change_percent = ((current_price - open_price) / open_price) * 100
            return change_percent, current_price
        else:
            return None, None
    except:
        return None, None

# --- KENAR ÇUBUĞU ---
with st.sidebar:
    st.title("🎛️ Kontrol Paneli")
    st.write("Sazlık Projesi - Web v3.1")
    
    api_key = st.text_input("Google Gemini API Key", type="password")
    
    st.divider()
    st.info("💡 **Garantici Mod Açık:**\nSistem global riskleri ve **anlık fiyat şişkinliğini** kontrol eder.")

# --- ANA EKRAN ---
st.title("🎯 SwingSniper: Sazlık Projesi")
st.markdown("**Durum:** `Sistem Aktif` | **Mod:** `Defansif / Aile Babası`")

# --- GELİŞMİŞ PROMPT ---
SYSTEM_PROMPT = """
**ROLE:**
Sen "Sazlık Projesi"nin Baş Stratejistisin. Kimliğin: Aşırı şüpheci, garantici ve defansif bir Swing Trader. 
Kullanıcın (Mert), sermayesi kısıtlı bir aile babasıdır. Kaybetme lüksü yoktur.

**GÖREV:**
Sana verilen finansal haberleri analiz et. Aşağıdaki "GÜVENLİK PROTOKOLÜ"nden geçmeyen her şeyi ELE.

**GÜVENLİK PROTOKOLÜ (4 KATMANLI FİLTRE):**
1. **GLOBAL İKLİM KONTROLÜ:** Piyasada genel bir çöküş, savaş riski veya teknoloji balonu patlaması (örn: Nvidia çöküşü) var mı? Varsa SİNYAL ÜRETME.
2. **HABER KALİTESİ:** Haber dedikodu mu? Elon Musk tweeti mi? Eğer öyleyse YOKSAY. Sadece şirketin kasasını etkileyecek gerçek haberlere bak.
3. **VADE KONTROL
