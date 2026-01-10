import streamlit as st
import pandas as pd
import json
import requests
import news_bot
import yfinance as yf
from datetime import datetime
from config import GITHUB_TOKEN, GIST_ID

st.set_page_config(page_title="Sazlık Projesi", page_icon="🦅", layout="wide")

# --- CSS (Terminal Tasarımı & Kartlar) ---
st.markdown("""
<style>
    /* Kart Tasarımları (Tab 1 için) */
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
    
    /* Terminal Satır Tasarımı (Tab 2 için) */
    .terminal-line {
        font-family: 'Courier New', monospace;
        font-size: 15px;
        padding: 4px 0;
        border-bottom: 1px dashed #333;
        color: #e6e6e6;
    }
    .term-icon { color: #4da6ff; margin-right: 8px; } /* Mavi Elmas Rengi */
    .term-ticker { font-weight: bold; color: #fff; }
    .term-val { color: #ccc; }
    .term-pnl-pos { color: #00ff41; font-weight: bold; } /* Matrix Yeşili */
    .term-pnl-neg { color: #ff4444; font-weight: bold; } /* Kırmızı */
    
    /* Özet Kutusu */
    .summary-box {
        background-color: #000;
        border: 1px solid #444;
        padding: 15px;
        font-family: 'Courier New', monospace;
        margin-top: 20px;
        color: #00ff41;
    }
</style>
""", unsafe_allow_html=True)

# --- VERİ YÖNETİMİ (GIST) ---
def get_portfolio():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        if r.status_code == 200:
            files = r.json().get('files', {})
            # Dosya adını dinamik alıyoruz ama sazlik_cuzdan.json olmasını bekliyoruz
            filename = list(files.keys())[0] 
            content = files[filename].get('content', '{}')
            return json.loads(content) if content else {}
        return {}
    except: return {}

def save_portfolio(portfolio):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        # Mevcut dosya adını koru veya sazlik_cuzdan.json yap
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

# Kasa Bilgisi (Sazlik_live.py mantığıyla aynı kalsın)
col_kasa, col_bos = st.columns([1, 3])
with col_kasa:
    kasa = st.number_input("💵 Kasa ($)", value=1000.0, step=100.0)

tab1, tab2 = st.tabs(["🔍 Tavşan Avı", "📜 Portföy (Z Raporu)"])

# --- TAB 1: TAVŞAN AVI (Gemini 3 Analizi) ---
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
                            st.button(f"✅ Zaten Var", key=btn_key, disabled=True)
                        else:
                            if st.button(f"AL: {stock['Hisse']}", key=btn_key):
                                adet = round(yatirim / stock['Fiyat'], 4)
                                current_portfolio[stock['Hisse']] = {
                                    "cost": stock['Fiyat'],
                                    "shares": adet,
                                    "date": str(datetime.now().date()),
                                    "stop": stock['Stop'],
                                    "target": stock['Hedef']
                                }
                                save_portfolio(current_portfolio)
                                st.toast(f"✅ {stock['Hisse']} Portföye Eklendi!", icon="🦅")
            else:
                st.warning("⚠️ Tavşan bulunamadı.")

# --- TAB 2: PORTFÖY (TERMİNAL GÖRÜNÜMÜ) ---
with tab2:
    st.subheader("📋 Portföy Kontrolü...")
    portfolio = get_portfolio()
    
    if portfolio:
        full_html = ""
        hisse_toplam_deger = 0
        
        for ticker, info in portfolio.items():
            if not isinstance(info, dict): continue

            # Verileri al
            shares = info.get('shares', 0)
            cost = info.get('cost', 0)
            
            # Anlık Fiyat Çek
            try:
                stock_data = yf.Ticker(ticker)
                hist = stock_data.history(period="1d")
                curr_price = hist['Close'].iloc[-1] if not hist.empty else cost
            except: curr_price = cost

            # Hesaplamalar
            val = curr_price * shares
            pnl_usd = (curr_price - cost) * shares
            pnl_pct = ((curr_price - cost) / cost * 100) if cost > 0 else 0
            
            hisse_toplam_deger += val
            
            # Renk Belirleme (Yeşil/Kırmızı)
            pnl_class = "term-pnl-pos" if pnl_usd >= 0 else "term-pnl-neg"
            sign = "+" if pnl_usd >= 0 else ""
            
            # TERMINAL SATIR FORMATI (HTML)
            line_html = f"""
            <div class="terminal-line">
                <span class="term-icon">🔹</span>
                <span class="term-ticker">{ticker}:</span> {curr_price:.2f}$ (x{shares}) | 
                <span class="term-val">Ort:</span> {cost:.2f}$ | 
                <span class="term-val">Değer:</span> {val:.0f}$ | 
                <span class="{pnl_class}">PNL: %{pnl_pct:.2f} ({sign}{pnl_usd:.1f}$)</span>
            </div>
            """
            full_html += line_html

        # Listeyi Bas
        st.markdown(full_html, unsafe_allow_html=True)
        
        # HESAP ÖZETİ (ASCII TARZI)
        toplam_servet = kasa + hisse_toplam_deger
        st.markdown(f"""
        <div class="summary-box">
        ========================================<br>
        📊 GÜNCEL HESAP ÖZETİ<br>
        ========================================<br>
        💵 Nakit (Boşta): {kasa:.2f} $<br>
        📈 Hisse Değeri:  {hisse_toplam_deger:.2f} $<br>
        💰 TOPLAM SERVET: {toplam_servet:.2f} $<br>
        ========================================
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.info("📂 sazlik_cuzdan.json dosyası boş veya okunamadı.")