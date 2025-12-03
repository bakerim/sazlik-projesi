import streamlit as st
import google.generativeai as genai
import feedparser
import json
import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- AYARLAR: PROFESYONEL QUANT ARAYÜZÜ ---
st.set_page_config(page_title="Sazlık Quant v9.1", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .main-header { font-family: 'Courier New', monospace; color: #fff; border-bottom: 2px solid #333; padding-bottom: 10px; }
    .trade-card {
        background-color: #161b22; border: 1px solid #30363d;
        border-radius: 8px; padding: 20px; margin-bottom: 20px;
    }
    .metric-box {
        background: #0d1117; border: 1px solid #21262d;
        padding: 10px; border-radius: 6px; text-align: center;
    }
    .metric-label { font-size: 0.75em; color: #8b949e; text-transform: uppercase; }
    .metric-val { font-size: 1.1em; font-weight: bold; color: #e6edf3; }
    .success-text { color: #3fb950; }
    .danger-text { color: #f85149; }
    .warning-text { color: #d29922; }
</style>
""", unsafe_allow_html=True)

# --- VERİ KAYNAKLARI (RSS) ---
RSS_URLS = [
    "https://www.kap.org.tr/rss",
    "https://news.google.com/rss/search?q=borsa+istanbul+şirket+haberleri&hl=tr&gl=TR&ceid=TR:tr",
    "https://finance.yahoo.com/news/rssindex",
]

# --- FONKSİYON 1: DİNAMİK DOĞRULAMA ---
def verify_ticker_math(ticker):
    if not ticker or ticker == "UNKNOWN": return None
    candidates = [ticker.upper(), f"{ticker.upper()}.IS"]
    for symbol in candidates:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            if not hist.empty:
                return symbol 
        except:
            continue
    return None

# --- FONKSİYON 2: QUANT TEKNİK FİLTRE ---
def quant_filter(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if len(df) < 50: return False, "Yetersiz Veri"
        
        ma_long = df['Close'].rolling(window=200).mean().iloc[-1] if len(df) > 200 else df['Close'].rolling(window=50).mean().iloc[-1]
        current_price = df['Close'].iloc[-1]
        
        # RSI HESAPLAMA
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # --- QUANT KURALLARI ---
        if rsi > 70:
            return False, f"⛔ FİLTRELENDİ: Fiyat şişmiş (RSI: {rsi:.1f})."
        if current_price < ma_long:
            return False, f"⛔ FİLTRELENDİ: Düşüş trendi (Fiyat < Ort). Ayı piyasası."

        return True, f"✅ ONAYLI: Trend Pozitif, Fiyat Makul (RSI: {rsi:.1f})"

    except Exception as e:
        return False, f"Veri Hatası: {e}"

# --- PROMPT ---
SYSTEM_PROMPT = """
**GÖREV:** Sen bir Algoritmik Ticaret Botusun. Duygu yok, sadece veri.
Sana verilen haberleri tara. Sadece **SOMUT NAKİT AKIŞI** (Bilanço, İhale, Temettü, Satın Alma) yaratan haberleri seç.

**KURALLAR:**
1. **TICKER:** Hisse kodunu bulamıyorsan o haberi YOK SAY. "UNKNOWN" kabul edilmez.
2. **NETLİK:** "Yükselebilir" değil, "İmzaladı", "Onaylandı" gibi kesin haberleri AL.

**ÇIKTI FORMATI (JSON):**
[
  {
    "Ticker": "THYAO",
    "Signal_Type": "İhale",
    "Reason": "Gerekçe...",
    "Target_Percent": 3.5,
    "Stop_Percent": 1.5,
    "Portfolio_Allocation": 10,
    "Hold_Days": 7
  }
]
"""

# --- ANA MOTOR ---
def run_analysis():
    if not st.session_state.get('api_key'):
        st.error("⚠️ Lütfen sol menüden API Anahtarını giriniz.")
        return

    genai.configure(api_key=st.session_state.api_key)
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=SYSTEM_PROMPT)
    status_box = st.empty()
    
    # 1. Haber Akışı
    status_box.info("📡 Veri akışı taranıyor...")
    headlines = []
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                headlines.append(f"- {entry.title}")
        except: pass
    
    if not headlines:
        st.error("Veri kaynağına ulaşılamadı.")
        return

    # 2. AI İşleme
    status_box.info("🧠 Algoritmik Analiz Çalışıyor...")
    try:
        response = model.generate_content("\n".join(headlines[:60]))
        opportunities = json.loads(response.text.replace('```json','').replace('```','').strip())
    except:
        st.warning("Uygun kriterde fırsat bulunamadı.")
        return
    
    status_box.empty()
    valid_count = 0

    # 3. İŞLEME VE FİLTRELEME
    for opp in opportunities:
        raw_ticker = opp.get('Ticker', '')
        
        # A. Doğrulama
        valid_ticker = verify_ticker_math(raw_ticker)
        if not valid_ticker: continue
            
        # B. Teknik Filtre
        is_safe, tech_msg = quant_filter(valid_ticker)
        if not is_safe: continue
            
        valid_count += 1
        
        # C. Tarih Hesaplama
        today = datetime.now()
        buy_date = today.strftime("%d.%m.%Y")
        sell_date = (today + timedelta(days=int(opp.get('Hold_Days', 7)))).strftime("%d.%m.%Y")
        
        # D. KARTLARI BAS (GİRİNTİSİZ HTML - DÜZELTİLDİ!)
        html_code = f"""
<div class="trade-card">
<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:10px;">
<h3 style="color:#fff;">💎 {valid_ticker}</h3>
<span style="background:#238636; color:white; padding:2px 8px; border-radius:4px; font-size:0.8em;">AL SİNYALİ</span>
</div>
<p style="margin-top:10px; color:#d0d7de;"><b>Gerekçe:</b> {opp['Reason']}</p>
<p style="font-size:0.8em; color:#8b949e;">{tech_msg}</p>
<div style="display:flex; justify-content:space-between; margin-top:15px;">
<div class="metric-box" style="width:23%;">
<div class="metric-label">Alım Tarihi</div>
<div class="metric-val">{buy_date}</div>
</div>
<div class="metric-box" style="width:23%;">
<div class="metric-label">Satış Tarihi</div>
<div class="metric-val">{sell_date}</div>
</div>
<div class="metric-box" style="width:23%;">
<div class="metric-label">Hedef</div>
<div class="metric-val success-text">+{opp['Target_Percent']}%</div>
</div>
<div class="metric-box" style="width:23%;">
<div class="metric-label">Stop Loss</div>
<div class="metric-val danger-text">-{opp['Stop_Percent']}%</div>
</div>
</div>
<div style="margin-top:15px; padding:10px; background:#161b22; border:1px dashed #30363d; text-align:center; border-radius:6px;">
<span style="color:#8b949e;">Önerilen Kasa Oranı:</span>
<span style="color:#fff; font-weight:bold;"> %{opp['Portfolio_Allocation']}</span>
</div>
</div>
"""
        st.markdown(html_code, unsafe_allow_html=True)

    if valid_count == 0:
        st.info("ℹ️ **Rapor:** 'Quant Standartlarına' uyan (Teknik + Temel) güvenli bir fırsat bulunamadı. Nakitte beklemek en iyi stratejidir.")

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Sazlık Quant")
    st.caption("v9.1 Görsel Düzeltme")
    st.session_state.api_key = st.text_input("API Key Giriniz", type="password")
    if st.button("ANALİZİ BAŞLAT 🚀", use_container_width=True):
        run_analysis()
