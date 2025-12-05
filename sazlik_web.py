import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import requests
import json

st.set_page_config(page_title="Sazlık Pro: 100", page_icon="🇺🇸", layout="wide")

# --- API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı Yok!")
    st.stop()

# --- CSS İLE GÖRSEL GÜZELLEŞTİRME ---
st.markdown("""
<style>
    .kasa-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #1e2130;
        border-left: 5px solid #ffd700;
        margin-bottom: 10px;
    }
    .sinyal-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #0e1117;
        border: 1px solid #30333d;
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
        
        trend = "YÜKSELİŞ (Bullish) 🟢" if price > sma20 else "DÜŞÜŞ (Bearish) 🔴"
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
    SEN BİR PORTFÖY YÖNETİCİSİSİN. RİSK ALMAYI SEVMEYEN "GARANTİCİ" BİR TARZIN VAR.
    
    VARLIK: {ticker} | FİYAT: ${price:.2f} | TREND: {trend} | VOLATİLİTE: %{vol:.2f}
    HABERLER: {news}
    
    GÖREV: Swing Trade analizi yap.
    
    ÇIKTIYI JSON FORMATINDA VER:
    {{
        "karar": "AL (LONG) veya SAT (SHORT) veya İZLE",
        "guven_skoru": (0-100 arası sayı),
        "analiz": "Kısa ve net yorum (maks 2 cümle)",
        "kasa_yonetimi": "Kasanın %X'i ile girilmeli. (Risk düşükse %10, yüksekse %5)",
        "giris": {price:.2f},
        "hedef": (Trende göre %3-%8 yukarısı),
        "stop": (Destek altı, %2-%4 aşağısı)
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '')
        return json.loads(text)
    except: return None

# --- ARAYÜZ ---
st.title("🇺🇸 Sazlık 100: Swing Radar")
st.caption("Otomatik Haber Botu & Garantici Risk Yönetimi")

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("🔍 Tarama")
    ticker = st.text_input("Hisse Kodu", "NVDA").upper()
    if st.button("Analiz Et", type="primary"):
        st.session_state['analiz_basladi'] = True

with col2:
    if st.session_state.get('analiz_basladi'):
        with st.spinner("Piyasa ve Haberler Taranıyor..."):
            price, trend, vol = get_technical_status(ticker)
            news_context = get_bot_news(ticker)
            
            if price:
                ai_data = ask_ai(ticker, price, trend, vol, news_context)
                
                if ai_data:
                    # KART TASARIMI
                    st.markdown(f"""
                    <div class="sinyal-box">
                        <h2>💎 KARAR: {ai_data['karar']}</h2>
                        <p><b>Güven Skoru:</b> %{ai_data['guven_skoru']} | <b>Risk:</b> {trend}</p>
                        <p>📝 <b>Analiz:</b> {ai_data['analiz']}</p>
                        <hr>
                        <div class="kasa-box">
                            💰 <b>Kasa Yönetimi:</b> {ai_data['kasa_yonetimi']}
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #ff4b4b;">🛑 <b>STOP:</b> ${ai_data['stop']}</span>
                            <span style="color: #00c853;">🎯 <b>HEDEF:</b> ${ai_data['hedef']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("Botun Yakaladığı Haberler"):
                        st.text(news_context)
                else:
                    st.error("AI Yanıt Vermedi.")
            else:
                st.error("Hisse Bulunamadı.")
