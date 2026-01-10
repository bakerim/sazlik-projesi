import streamlit as st
import pandas as pd
import json
import requests
import news_bot
import yfinance as yf
from datetime import datetime
from config import GITHUB_TOKEN, GIST_ID

st.set_page_config(page_title="Sazlık Projesi", page_icon="🦅", layout="wide")

# --- CSS (Terminal & Matrix Tasarımı) ---
st.markdown("""
<style>
    /* Kart Tasarımları (Tab 1) */
    .card {
        background-color: #0e1117;
        border: 1px solid #30333d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header-row { display: flex; justify_content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 5px; }
    .ticker-text { font-size: 22px; font-weight: 900; color: #fff; }
    .score-tag { font-size: 14px; font-weight: bold; color: #000; padding: 2px 10px; border-radius: 15px; }
    .ai-section { background-color: rgba(77, 166, 255, 0.1); border-left: 3px solid #4da6ff; padding: 8px; font-size: 12px; color: #ccc; margin-bottom: 10px; }
    .data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-family: 'Courier New', monospace; font-size: 12px; }
    
    /* Z RAPORU (Tab 2) - Terminal Stili */
    .terminal-container {
        background-color: #000;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        margin-bottom: 20px;
    }
    .term-line {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px dashed #333;
        padding: 8px 0;
        font-size: 14px;
    }
    .term-left { display: flex; gap: 10px; align-items: center; }
    .term-right { text-align: right; }
    
    .t-date { color: #888; font-size: 12px; }
    .t-ticker { color: #4da6ff; font-weight: bold; font-size: 16px; }
    .t-details { color: #ccc; font-size: 13px; }
    
    .pnl-plus { color: #00ff41; font-weight: bold; }
    .pnl-minus { color: #ff4444; font-weight: bold; }
    
    /* Özet Paneli */
    .summary-panel {
        background-color: #111;
        border: 2px solid #444;
        padding: 20px;
        color: #00ff41;
        font-family: 'Courier New', monospace;
        font-size: 15px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- GIST BAĞLANTISI (Cüzdan Okuma/Yazma) ---
def get_portfolio():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        if r.status_code == 200:
            files = r.json().get('files', {})
            # Dosya adını otomatik bul
            filename = list(files.keys())[0]
            content = files[filename].get('content', '{}')
            return json.loads(content) if content else {}
        return {}
    except: return {}

def save_portfolio(portfolio):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        filename = list(r.json()['files'].keys())[0] if r.status_code == 200 else "sazlik_cuzdan.json"
        data = {"files": {filename: {"content": json.dumps(portfolio, indent=4)}}}
        requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=data)
    except: pass

def create_card(stock, yatirim):
    if stock['Guven_Skoru'] >= 85: color = "#00ff41" 
    elif stock['Guven_Skoru'] >= 75: color = "#4da6ff" 
    else: color = "#ffbb00" 

    html = f"""
    <div class="card" style="border-top: 3px solid {color};">
        <div class="header-row">
            <span class="ticker-text" style="color:{color}">{stock['Hisse']}</span>
            <span class="score-tag" style="background-color:{color}">{stock['Guven_Skoru']:.1f}</span>
        </div>
        <div class="ai-section">🧠 {stock['AI_Notu']}</div>
        <div class="data-grid">
            <div style="display:flex; justify-content:space-between;"><span>Fiyat:</span> <span style="color:#fff">${stock['Fiyat']:.2f}</span></div>
            <div style="display:flex; justify-content:space-between;"><span>Potansiyel:</span> <span style="color:{color}">%{stock['Pot_Kar']:.2f}</span></div>
            <div style="display:flex; justify-content:space-between;"><span>Stop:</span> <span style="color:#ff4444">${stock['Stop']:.2f}</span></div>
            <div style="display:flex; justify-content:space-between;"><span>Hedef:</span> <span style="color:#00ff41">${stock['Hedef']:.2f}</span></div>
        </div>
        <div style="margin-top:10px; text-align:right; border-top:1px solid #333; padding-top:5px;">
             <span style="font-size:16px; font-weight:bold; color:#fff;">Giriş: ${yatirim}</span>
        </div>
    </div>
    """
    return html

# --- ARAYÜZ ---
st.title("🦅 SAZLIK - MAĞARA ADAMI & GEMINI 3")

col_kasa, col_bos = st.columns([1, 3])
with col_kasa:
    kasa = st.number_input("💵 Kasa ($)", value=1000.0, step=100.0)

tab1, tab2 = st.tabs(["🔍 Tavşan Avı", "📜 Z Raporu (Cüzdan)"])

# --- TAB 1: TAVŞAN AVI ---
with tab1:
    if st.button("🚀 TARAMAYI BAŞLAT", type="primary"):
        with st.spinner("Gemini 3 avlanıyor..."):
            top_picks = news_bot.run_analysis_engine()
            if top_picks:
                st.success(f"🦁 Elit 6 Finalist Hazır!")
                current_portfolio = get_portfolio()
                cols = st.columns(3)
                for i, stock in enumerate(top_picks):
                    if stock['Guven_Skoru'] >= 85: ratio = 0.25
                    elif stock['Guven_Skoru'] >= 75: ratio = 0.20
                    else: ratio = 0.15
                    yatirim = round(kasa * ratio, 2)
                    
                    with cols[i % 3]:
                        st.markdown(create_card(stock, yatirim), unsafe_allow_html=True)
                        btn_key = f"btn_{stock['Hisse']}_{datetime.now().timestamp()}"
                        if stock['Hisse'] in current_portfolio:
                            st.button(f"✅ Portföyde Var", key=btn_key, disabled=True)
                        else:
                            if st.button(f"AL: {stock['Hisse']}", key=btn_key):
                                adet = round(yatirim / stock['Fiyat'], 4)
                                current_portfolio[stock['Hisse']] = {
                                    "cost": stock['Fiyat'],
                                    "shares": adet,
                                    "date": str(datetime.now().date()), # Tarih eklendi
                                    "stop": stock['Stop'],
                                    "target": stock['Hedef']
                                }
                                save_portfolio(current_portfolio)
                                st.toast(f"✅ {stock['Hisse']} eklendi!", icon="🦅")
            else:
                st.warning("⚠️ Tavşan bulunamadı.")

# --- TAB 2: Z RAPORU (CANLI TAKİP) ---
with tab2:
    st.subheader("📡 Sazlık Live: Portföy Durumu")
    
    # Gist'ten veriyi çek
    portfolio = get_portfolio()
    
    if portfolio:
        html_content = '<div class="terminal-container">'
        
        # Toplamlar için değişkenler
        toplam_yatirilan = 0
        toplam_guncel_deger = 0
        
        for ticker, info in portfolio.items():
            if not isinstance(info, dict): continue

            # Verileri Gist'ten güvenli çek
            shares = info.get('shares', 0)
            cost = info.get('cost', 0)
            date = info.get('date', '---') # Tarih yoksa çizgi koy
            
            # Güncel fiyatı yfinance ile çek
            try:
                stock_data = yf.Ticker(ticker)
                hist = stock_data.history(period="1d")
                curr_price = hist['Close'].iloc[-1] if not hist.empty else cost
            except: 
                curr_price = cost

            # Matematik
            invested = cost * shares
            current_val = curr_price * shares
            pnl_usd = current_val - invested
            pnl_pct = (pnl_usd / invested * 100) if invested > 0 else 0
            
            # Genel Toplamlara Ekle
            toplam_yatirilan += invested
            toplam_guncel_deger += current_val

            # Renkler
            color_cls = "pnl-plus" if pnl_usd >= 0 else "pnl-minus"
            sign = "+" if pnl_usd >= 0 else ""
            
            # HTML SATIR (Terminal Görünümü)
            row_html = f"""
            <div class="term-line">
                <div class="term-left">
                    <span style="color:#4da6ff;">🔹</span>
                    <div>
                        <div class="t-ticker">{ticker} <span class="t-date">({date})</span></div>
                        <div class="t-details">Maliyet: {cost:.2f}$ | Adet: {shares}</div>
                    </div>
                </div>
                <div class="term-right">
                    <div style="font-size:15px; color:#fff;">{current_val:.0f} $</div>
                    <div class="{color_cls}">PNL: %{pnl_pct:.2f} ({sign}{pnl_usd:.1f}$)</div>
                </div>
            </div>
            """
            html_content += row_html
            
        html_content += '</div>'
        st.markdown(html_content, unsafe_allow_html=True)
        
        # --- ÖZET TABLOSU ---
        toplam_kar_zarar = toplam_guncel_deger - toplam_yatirilan
        genel_kar_orani = (toplam_kar_zarar / toplam_yatirilan * 100) if toplam_yatirilan > 0 else 0
        toplam_servet = kasa + toplam_guncel_deger
        
        summary_html = f"""
        <div class="summary-box">
        ========================================<br>
        🦅 SAZLIK FİNANSAL Z RAPORU<br>
        ========================================<br>
        💰 Nakit Bakiye   : {kasa:.2f} $<br>
        🏦 Hisse Değeri   : {toplam_guncel_deger:.2f} $<br>
        💎 TOPLAM SERVET  : {toplam_servet:.2f} $<br>
        ----------------------------------------<br>
        📊 TOPLAM YATIRIM : {toplam_yatirilan:.2f} $<br>
        🚀 NET KAR/ZARAR  : {toplam_kar_zarar:+.2f} $ <br>
        📈 GENEL KAR ORANI: %{genel_kar_orani:+.2f}<br>
        ========================================
        </div>
        """
        st.markdown(f"<style>.summary-box {{ background-color:#111; border:2px solid #444; padding:20px; color:#00ff41; font-family:'Courier New'; line-height:1.6; }}</style>{summary_html}", unsafe_allow_html=True)
        
    else:
        st.info("📭 Portföy boş. Gist bağlantısını kontrol et veya alım yap.")