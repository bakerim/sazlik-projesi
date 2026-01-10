import streamlit as st
import pandas as pd
import json
import requests
import news_bot
import yfinance as yf
from datetime import datetime
from config import GITHUB_TOKEN, GIST_ID

st.set_page_config(page_title="Sazlık Projesi", page_icon="🦅", layout="wide")

# --- CSS (Terminal Tasarımı) ---
st.markdown("""
<style>
    .card { background-color: #0e1117; border: 1px solid #30333d; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    .ticker-text { font-size: 24px; font-weight: 900; color: #4da6ff; }
    .ai-section { background-color: rgba(77, 166, 255, 0.1); border-left: 3px solid #4da6ff; padding: 10px; font-size: 13px; color: #ccc; font-style: italic; }
    
    /* Z RAPORU TERMİNAL TASARIMI */
    .terminal-box { background-color: #000; border: 1px solid #333; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; }
    .term-row { display: flex; justify-content: space-between; border-bottom: 1px dashed #222; padding: 10px 0; }
    .pnl-pos { color: #00ff41; font-weight: bold; }
    .pnl-neg { color: #ff4444; font-weight: bold; }
    .term-header { color: #888; font-size: 12px; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- VERİ ÇEKME (YENİ JSON YAPISINA UYGUN) ---
def get_full_data():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        if r.status_code == 200:
            files = r.json().get('files', {})
            filename = list(files.keys())[0]
            content = files[filename].get('content', '{}')
            return json.loads(content)
    except: return {}

# --- ARAYÜZ ---
st.title("🦅 SAZLIK PRO - Z RAPORU")

# JSON Verisini Çek
full_data = get_full_data()
bakiye_gist = full_data.get('bakiye', 1000.0)

col_kasa, _ = st.columns([1, 3])
with col_kasa:
    kasa = st.number_input("💵 Kasa ($)", value=float(bakiye_gist), step=100.0)

tab1, tab2 = st.tabs(["🔍 Tavşan Avı (79+)", "📜 Z Raporu (Cüzdan)"])

# --- TAB 1: TAVŞAN AVI ---
with tab1:
    if st.button("🚀 TARAMAYI BAŞLAT", type="primary"):
        with st.spinner("Teknik tarama ve Gemini 3 toplu analiz yapılıyor..."):
            top_picks = news_bot.run_analysis_engine()
            if top_picks:
                st.success("🦁 Elit Finalistler Hazır!")
                cols = st.columns(3)
                for i, stock in enumerate(top_picks):
                    color = "#00ff41" if stock['Guven_Skoru'] >= 85 else "#4da6ff"
                    yatirim = round(kasa * (0.25 if stock['Guven_Skoru'] >= 85 else 0.20), 2)
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div class="card" style="border-top: 4px solid {color};">
                            <div style="display:flex; justify-content:space-between;">
                                <span class="ticker-text">{stock['Hisse']}</span>
                                <span style="background:{color}; color:#000; padding:2px 10px; border-radius:10px; font-weight:bold;">{stock['Guven_Skoru']:.1f}</span>
                            </div>
                            <div class="ai-section">🧠 {stock['AI_Notu']}</div>
                            <div style="font-family:monospace; font-size:12px; margin-top:10px;">
                                <div>Fiyat: ${stock['Fiyat']:.2f} | Hedef: ${stock['Hedef']:.2f}</div>
                            </div>
                            <div style="text-align:right; margin-top:10px; font-weight:bold; color:#fff;">Yatırım: ${yatirim}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ 79 puan barajını aşan hisse bulunamadı.")

# --- TAB 2: Z RAPORU (PORTFÖY) ---
with tab2:
    st.subheader("📊 Canlı Portföy Durumu")
    
    portfolio_dict = full_data.get('portfoy', {})
    
    if portfolio_dict:
        t_invested, t_current = 0, 0
        html_out = '<div class="terminal-box">'
        html_out += '<div class="term-header">HİSSE (TARİH) | ADET @ MALİYET | GÜNCEL DEĞER | PNL</div>'
        
        for ticker, info in portfolio_dict.items():
            shares = info.get('adet', 0)
            cost = info.get('maliyet', 0)
            date = info.get('tarih', '---')
            
            # Yahoo'dan anlık fiyat çek
            try:
                curr_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
            except: curr_price = cost
            
            val = curr_price * shares
            invested = cost * shares
            pnl = val - invested
            pnl_p = (pnl / invested * 100) if invested > 0 else 0
            
            t_invested += invested
            t_current += val
            
            cls = "pnl-pos" if pnl >= 0 else "pnl-neg"
            html_out += f"""
            <div class="term-row">
                <span><b style="color:#4da6ff;">{ticker}</b> <small style="color:#666;">({date})</small><br>
                <small style="color:#888;">{shares} Adet @ {cost:.2f}$</small></span>
                <span style="text-align:right;"><b style="color:#fff;">{val:.1f}$</b><br>
                <small class="{cls}">%{pnl_p:.2f} ({pnl:+.1f}$)</small></span>
            </div>
            """
        html_out += "</div>"
        st.markdown(html_out, unsafe_allow_html=True)
        
        # --- FİNANSAL ÖZET ---
        net_pnl = t_current - t_invested
        net_p_p = (net_pnl / t_invested * 100) if t_invested > 0 else 0
        
        st.code(f"""
==================================================
💰 Nakit (Bakiye) : {kasa:.2f}$
📈 Hisse Değeri    : {t_current:.2f}$
💎 TOPLAM SERVET   : {kasa + t_current:.2f}$
--------------------------------------------------
🚀 Toplam Kar/Zarar: {net_pnl:+.2f}$ (%{net_p_p:+.2f})
==================================================""")

        # Cezalılar Bölümü
        cezalar = full_data.get('cezalar', {})
        if cezalar:
            st.warning(f"🚫 CEZALI HİSSELER: {', '.join(cezalar.keys())}")
    else:
        st.info("📂 Cüzdan boş veya 'portfoy' anahtarı bulunamadı.")