import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Sazlık: Fırsat Sıralaması", page_icon="🏆", layout="wide")

# --- API KONTROL ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı Yok! Streamlit Secrets ayarlarını yapmalısın.")
    st.stop()

# --- CSS TASARIMI (PUANA GÖRE RENKLER) ---
st.markdown("""
<style>
    /* Kartların Genel Yapısı */
    .card {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .card:hover { transform: scale(1.02); }
    
    /* Puan Rozeti */
    .score-badge {
        background: rgba(255,255,255,0.2);
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.1em;
        float: right;
    }
    
    /* İçerik Düzeni */
    .card-header { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .analysis-text { font-size: 15px; opacity: 0.9; margin-bottom: 15px; min-height: 60px; }
    
    /* Strateji Kutusu */
    .strategy-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 5px;
        background: rgba(0,0,0,0.25);
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
    .stat-label { font-size: 11px; color: #ccc; text-transform: uppercase; }
    .stat-val { font-size: 16px; font-weight: bold; }
    
    /* Renk Sınıfları */
    .tier-s { background: linear-gradient(135deg, #1b5e20 0%, #00e676 100%); border: 2px solid #00e676; } /* 90+ */
    .tier-a { background: linear-gradient(135deg, #0d47a1 0%, #2979ff 100%); border: 2px solid #2979ff; } /* 75-89 */
    .tier-b { background: linear-gradient(135deg, #bf360c 0%, #ff6d00 100%); border: 2px solid #ff6d00; } /* 60-74 */
</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---

def get_technical_filter(ticker):
    """
    Sadece Yükseliş trendindekileri alalım. 
    Düşüştekiler 'Sıralamaya' bile girmesin, zaman kaybı.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if hist.empty: return None
        
        price = hist['Close'].iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        
        if price < sma20: return None # Trend Kötü
        
        return {"price": price}
    except: return None

def get_news_leads():
    url = "https://raw.githubusercontent.com/bakerim/sazlik-projesi/main/news_archive.json"
    try:
        data = requests.get(url).json()
        leads = {}
        for item in data:
            ticker = item.get('ticker')
            if ticker not in leads: leads[ticker] = []
            leads[ticker].append(f"- {item['content']}")
        return leads
    except: return {}

def score_opportunity(ticker, tech_data, news_list):
    """
    AI artık 'Uygun mu?' diye sormuyor, 'Kaç Puan?' diye soruyor.
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    news_text = "\n".join(news_list[:3])
    
    prompt = f"""
    SEN "GARANTİCİ BABA" LAKAPLI TRADER'SIN.
    
    HİSSE: {ticker} | FİYAT: ${tech_data['price']:.2f} (Teknik: YÜKSELİŞ Trendi)
    HABERLER:
    {news_text}
    
    GÖREV: Bu swing trade fırsatına 0 ile 100 arası bir GÜVEN PUANI ver.
    
    PUANLAMA MANTIĞI:
    - 90-100: "Gözü Kapalı Alınır" (Haber çok iyi + Trend güçlü)
    - 75-89: "Güzel Fırsat" (Risk düşük, potansiyel var)
    - 60-74: "Riskli ama Denenebilir" (Stoplu takip şart)
    - 0-59: "Bulaşma" (Pas geç)
    
    ÇIKTI (JSON):
    {{
        "puan": (Sayı),
        "baslik": "Kısa Çarpıcı Başlık (Örn: ROKET HAZIRLIĞI)",
        "analiz": "Neden bu puanı verdin? (Maks 2 cümle)",
        "giris": {tech_data['price']:.2f},
        "hedef": (Makul kar al),
        "stop": (Stop noktası),
        "vade": "X Gün"
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('
