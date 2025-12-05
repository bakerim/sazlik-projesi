import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import requests
import json

st.set_page_config(page_title="Sazlık 100 Pro", page_icon="🇺🇸", layout="wide")

# --- API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı Yok!")
    st.stop()

# --- CSS İLE KART TASARIMI ---
st.markdown("""
<style>
    .card {
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .card-header {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }
    .kasa-badge {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 14px;
        margin-top: 10px;
        border-left: 3px solid #FFD700;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        margin-top: 15px;
        font-size: 16px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def get_technical_status(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if hist.empty: return None, "Yok", 0
        
        price = hist['Close'].iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        daily_range = (hist['High'] - hist['Low']).mean()
        volatility = (daily_range / price) * 100
        
        trend = "YÜKSELİŞ 🟢" if price > sma20 else "DÜŞÜŞ 🔴"
        return price, trend, volatility
    except: return None, "Hata", 0

def get_bot_news(ticker):
    url = "https://raw.githubusercontent.com/bakerim/sazlik-projesi/main/news_archive.json"
    try:
        data = requests.get(url).json()
        news = [f"- [{i['date']}] {i['content']}" for i in data if i.get('ticker') == ticker]
        return "\n".join(news[:3]) if news else "Bot henüz bu hisse için haber yakalamadı."
    except: return "Veri Hatası"

def ask_ai(ticker, price, trend, vol, news):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    prompt = f"""
    SEN "GARANTİCİ BABA" LAKAPLI BİR FON YÖNETİCİSİSİN.
    
    HİSSE: {ticker} | FİYAT: ${price:.2f} | TREND: {trend} | VOLATİLİTE: %{vol:.2f}
    HABERLER: {news}
    
    GÖREV: Swing Trade analizi yap.
    
    ÖNEMLİ: 
    - Kararın "AL" ise, neden güvenli olduğunu anlat.
    - Kararın "İZLE" veya "SAT" ise riskleri vurgula.
    - Kasa yönetimi konusunda cimri ol.
    
    ÇIKTIYI JSON FORMATINDA VER:
    {{
        "karar": "AL (FIRSAT) veya SAT (RİSKLİ) veya İZLE (NÖTR)",
        "guven_skoru": (0-100 arası sayı),
        "analiz": "Kısa ve net yorum.",
        "kasa_yonetimi": "Kasanın %X'i. (Gerekçesi)",
        "hedef": (Dolar fiyatı),
        "stop": (Dolar fiyatı)
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '')
        return json.loads(text)
    except: return None

# --- ARAYÜZ ---
st.title("🇺🇸 Sazlık 100: Swing Radar")

col1, col2 = st.columns([1, 3])

with col1:
    ticker = st.text_input("Hisse Kodu", "NVDA").upper()
    if st.button("ANALİZİ BAŞLAT 🚀", type="primary"):
        st.session_state['run'] = True

with col2:
    if st.session_state.get('run'):
        with st.spinner("Piyasa taranıyor..."):
            price, trend, vol = get_technical_status(ticker)
            news_context = get_bot_news(ticker)
            
            if price:
                ai_data = ask_ai(ticker, price, trend, vol, news_context)
                
                if ai_data:
                    # RENK AYARLAMASI
                    karar = ai_data['karar'].upper()
                    if "AL" in karar:
                        bg_color = "#1b5e20" # Koyu Yeşil
                        border = "2px solid #00e676"
                        icon = "💎"
                    elif "SAT" in karar:
                        bg_color = "#b71c1c" # Koyu Kırmızı
                        border = "2px solid #ff5252"
                        icon = "🔻"
                    else: # İZLE
                        bg_color = "#0d47a1" # Koyu Mavi
                        border = "2px solid #2979ff"
                        icon = "👀"

                    # HTML KARTININ OLUŞTURULMASI
                    st.markdown(f"""
                    <div class="card" style="background-color: {bg_color}; border: {border};">
                        <div class="card-header">
                            {icon} {ai_data['karar']}
                            <span style="margin-left: auto; font-size: 16px; opacity: 0.8;">Güven: %{ai_data['guven_skoru']}</span>
                        </div>
                        <p style="font-size: 16px;">{ai_data['analiz']}</p>
                        
                        <div class="kasa-badge">
                            💰 <b>Kasa Yönetimi:</b> {ai_data['kasa_yonetimi']}
                        </div>
                        
                        <div class="metric-row">
                            <span style="color: #ff8a80;">🛑 STOP: ${ai_data['stop']}</span>
                            <span>🏷️ Giriş: ${price:.2f}</span>
                            <span style="color: #b9f6ca;">🎯 HEDEF: ${ai_data['hedef']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("Botun Yakaladığı Haberler"):
                        st.info(news_context)
                else:
                    st.error("AI Bağlantı Hatası")
            else:
                st.error("Hisse Bulunamadı")
