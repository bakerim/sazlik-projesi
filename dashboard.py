import streamlit as st
import pandas as pd
import json
import requests
import news_bot
import yfinance as yf
from datetime import datetime
from config import GITHUB_TOKEN, GIST_ID

st.set_page_config(page_title="Sazlık Projesi", page_icon="🦅", layout="wide")

# --- CSS (Matrix/Terminal Stili) ---
st.markdown("""
<style>
    .card { background-color: #0e1117; border: 1px solid #30333d; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    .ticker-text { font-size: 24px; font-weight: 900; color: #4da6ff; }
    .ai-section { background-color: rgba(77, 166, 255, 0.1); border-left: 3px solid #4da6ff; padding: 10px; font-size: 13px; color: #ccc; font-style: italic; }
    .terminal-box { background-color: #000; border: 1px solid #333; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; }
    .term-row { display: flex; justify-content: space-between; border-bottom: 1px dashed #222; padding: 10px 0; }
    .pnl-pos { color: #00ff41; font-weight: bold; }
    .pnl-neg { color: #ff4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- GIST BAĞLANTISI ---
def get_portfolio():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        if r.status_code == 200:
            files = r.json().get('files', {})
            filename = list(files.keys())[0]
            content = files[filename].get('content', '{}')
            return json.loads(content) if content else {}
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
    color = "#00ff41" if stock['Guven_Skoru'] >= 85 else "#4da6ff"
    return f"""
    <div class="card" style="border-top: 4px solid {color};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="ticker-text">{stock['Hisse']}</span>
            <span style="background:{color}; color:#000; padding:2px 10px; border-radius:10px; font-weight:bold;">{stock['Guven_Skoru']:.1f}</span>
        </div>
        <div class="ai-section">🧠 {stock['AI_Notu']}</div>
        <div style="font-family:monospace; font-size:12px; margin-top:10px;">
            <div style="display:flex; justify-content:space-between;"><span>Fiyat:</span><span>${stock['Fiyat']:.2f}</span></div>
            <div style="display:flex; justify-content:space-between; color:{color};"><span>Hedef:</span><span>${stock['Hedef']:.2f}</span></div>
            <div style="display:flex; justify-content:space-between; color:#ff4444;"><span>Stop:</span><span>${stock['Stop']:.2f}</span></div>
        </div>
        <div style="text-align:right; margin-top:10px; font-weight:bold; color:#fff; border-top:1px solid #333; padding-top:5px;">
            Yatırım: ${yatirim}
        </div>
    </div>
    """

# --- ANA ARAYÜZ ---
st.title("🦅 SAZLIK PRO - Z RAPORU")

col_kasa, _ = st.columns([1, 3])
with col_kasa:
    kasa = st.number_input("💵 Kasa ($)", value=1000.0, step=100.0)

tab1, tab2 = st.tabs(["🔍 Tavşan Avı (79+)", "📜 Z Raporu (Cüzdan)"])

with tab1:
    if st.button("🚀 TARAMAYI BAŞLAT", type="primary"):
        with st.spinner("Teknik süzgeç ve Gemini 3 toplu analizi yapılıyor..."):
            top_picks = news_bot.run_analysis_engine()
            if top_picks:
                st.success("🦁 Elit Finalistler Hazır!")
                current_portfolio = get_portfolio()
                cols = st.columns(3)
                for i, stock in enumerate(top_picks):
                    ratio = 0.25 if stock['Guven_Skoru'] >= 85 else 0.20
                    yatirim = round(kasa * ratio, 2)
                    with cols[i % 3]:
                        st.markdown(create_card(stock, yatirim), unsafe_allow_html=True)
                        if st.button(f"AL: {stock['Hisse']}", key=f"al_{stock['Hisse']}"):
                            current_portfolio[stock['Hisse']] = {
                                "cost": stock['Fiyat'], "shares": round(yatirim/stock['Fiyat'], 4),
                                "date": str(datetime.now().date()), "stop": stock['Stop'], "target": stock['Hedef']
                            }
                            save_portfolio(current_portfolio)
                            st.toast(f"{stock['Hisse']} Alındı!")
            else:
                st.warning("⚠️ 79 puan barajını aşan hisse bulunamadı.")

with tab2:
    st.subheader("📊 Canlı Portföy Durumu")
    portfolio = get_portfolio()
    if portfolio:
        t_invested, t_current = 0, 0
        html_out = '<div class="terminal-box">'
        
        for ticker, info in portfolio.items():
            if not isinstance(info, dict) or ticker in ["PORTFOY", "CEZALAR"]: continue
            
            shares = info.get('shares', 0)
            cost = info.get('cost', 0)
            try:
                curr_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
            except: curr_price = cost
            
            val = curr_price * shares
            pnl = val - (cost * shares)
            pnl_p = (pnl / (cost * shares) * 100) if cost > 0 else 0
            t_invested += (cost * shares)
            t_current += val
            
            cls = "pnl-pos" if pnl >= 0 else "pnl-neg"
            html_out += f"""
            <div class="term-row">
                <span><b style="color:#4da6ff;">{ticker}</b> <small style="color:#666;">({info.get('date','-')})</small><br>
                <small style="color:#888;">{shares} Adet @ {cost:.2f}$</small></span>
                <span style="text-align:right;"><b style="color:#fff;">{val:.1f}$</b><br>
                <small class="{cls}">%{pnl_p:.2f} ({pnl:+.1f}$)</small></span>
            </div>
            """
        html_out += "</div>"
        st.markdown(html_out, unsafe_allow_html=True)
        
        net_pnl = t_current - t_invested
        st.code(f"""
========================================
💰 Nakit: {kasa:.2f}$ | 💎 Toplam Servet: {kasa + t_current:.2f}$
🚀 Toplam PNL: {net_pnl:+.2f}$ (%{(net_pnl/t_invested*100) if t_invested > 0 else 0:+.2f})
========================================""")
    else: st.info("Cüzdan boş.")