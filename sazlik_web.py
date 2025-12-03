import streamlit as st
import google.generativeai as genai
import feedparser
import json
import yfinance as yf
from datetime import datetime, timedelta

# --- AYARLAR ---
st.set_page_config(page_title="Sazlık v10.0: Native", page_icon="🏛️", layout="wide")

# --- KAYNAKLAR ---
RSS_URLS = [
    "https://www.kap.org.tr/rss",
    "https://news.google.com/rss/search?q=borsa+istanbul+şirket+haberleri&hl=tr&gl=TR&ceid=TR:tr",
    "https://finance.yahoo.com/news/rssindex",
]

# --- FONKSİYON 1: DOĞRULAMA ---
def verify_ticker(ticker):
    if not ticker or ticker == "UNKNOWN": return None
    candidates = [ticker.upper(), f"{ticker.upper()}.IS"]
    for symbol in candidates:
        try:
            stock = yf.Ticker(symbol)
            if not stock.history(period="1d").empty:
                return symbol
        except: continue
    return None

# --- FONKSİYON 2: TEKNİK FİLTRE ---
def quant_filter(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if len(df) < 50: return False, "Yetersiz Veri"
        
        current = df['Close'].iloc[-1]
        # Trend (SMA 50/200)
        ma_long = df['Close'].rolling(window=200).mean().iloc[-1] if len(df) > 200 else df['Close'].rolling(window=50).mean().iloc[-1]
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        if rsi > 70: return False, f"⚠️ RSI Şişmiş ({rsi:.1f})"
        if current < ma_long: return False, f"⚠️ Düşüş Trendi (Fiyat < Ort)"
        
        return True, f"✅ Teknik Uygun (RSI: {rsi:.1f})"
    except: return False, "Veri Hatası"

# --- PROMPT ---
SYSTEM_PROMPT = """
**GÖREV:** Borsa haberlerini tara. Sadece SOMUT NAKİT AKIŞI (Bilanço, İhale, Temettü) olanları seç.
**KURAL:** Hisse kodunu (Ticker) bilmiyorsan o haberi YOK SAY.
**ÇIKTI:**
[
  {
    "Ticker": "THYAO",
    "Reason": "Yeni uçak alımı...",
    "Target_Percent": 5,
    "Stop_Percent": 2,
    "Portfolio_Allocation": 10,
    "Hold_Days": 7
  }
]
"""

# --- ANA MOTOR ---
def run_analysis():
    if not st.session_state.get('api_key'):
        st.error("⚠️ API Key Giriniz")
        return

    genai.configure(api_key=st.session_state.api_key)
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=SYSTEM_PROMPT)
    
    with st.spinner('📡 Piyasalar taranıyor ve analiz ediliyor...'):
        headlines = []
        for url in RSS_URLS:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:8]: headlines.append(f"- {entry.title}")
            except: pass
        
        if not headlines:
            st.error("Haber bulunamadı.")
            return

        try:
            resp = model.generate_content("\n".join(headlines[:60]))
            opps = json.loads(resp.text.replace('```json','').replace('```','').strip())
        except:
            st.warning("Fırsat bulunamadı.")
            return

        valid_count = 0
        
        for opp in opps:
            raw = opp.get('Ticker', '')
            valid = verify_ticker(raw)
            if not valid: continue
            
            is_safe, tech_msg = quant_filter(valid)
            if not is_safe: continue
            
            valid_count += 1
            
            # --- TARİHLER ---
            today = datetime.now()
            sell_date = today + timedelta(days=int(opp.get('Hold_Days', 7)))
            
            # --- EKRANA BASMA (NATIVE UI - SAF STREAMLIT) ---
            # Artık HTML yok, Streamlit'in kendi güzel kutuları var.
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"💎 {valid} (AL)")
                    st.caption(f"📅 Satış Hedefi: {sell_date.strftime('%d.%m.%Y')}")
                with col2:
                    st.success(f"Hedef: +%{opp['Target_Percent']}")
                
                st.write(f"**Gerekçe:** {opp['Reason']}")
                st.info(f"📊 {tech_msg}")
                
                # Metrikleri yan yana dizelim
                m1, m2, m3 = st.columns(3)
                m1.metric("Stop Loss", f"-{opp['Stop_Percent']}%", delta_color="inverse")
                m2.metric("Vade", f"{opp['Hold_Days']} Gün")
                m3.metric("Kasa Oranı", f"%{opp['Portfolio_Allocation']}")

        if valid_count == 0:
            st.info("🤷‍♂️ Kriterlere uyan güvenli fırsat bulunamadı.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏛️ Sazlık v10")
    st.session_state.api_key = st.text_input("API Key", type="password")
    if st.button("ANALİZ ET 🚀", use_container_width=True):
        run_analysis()
