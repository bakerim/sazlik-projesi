import streamlit as st
import pandas as pd
import json
import requests
import news_bot
import yfinance as yf
from datetime import datetime
from config import GITHUB_TOKEN, GIST_ID

st.set_page_config(page_title="Sazlık Pro v2", page_icon="🦅", layout="wide")

# --- GELİŞMİŞ CSS (MATRIX & TERMINAL RENKLERİ) ---
st.markdown("""
<style>
    /* Kartlar (Tab 1) */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #0e1117; border-radius: 5px; }
    
    .card { background-color: #0e1117; border: 1px solid #30333d; border-radius: 12px; padding: 16px; margin-bottom: 16px; border-top: 4px solid #4da6ff; }
    .ticker-text { font-size: 24px; font-weight: 900; color: #4da6ff; }
    
    /* Tablo Renkleri (Tab 2) */
    .pnl-plus { color: #00ff41; font-weight: bold; }
    .pnl-minus { color: #ff4444; font-weight: bold; }
    .stop-warning { background-color: rgba(255, 68, 68, 0.2); border-left: 5px solid #ff4444; padding: 5px; }
    .target-success { background-color: rgba(0, 255, 65, 0.2); border-left: 5px solid #00ff41; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# --- VERİ YÖNETİMİ ---
def get_full_data():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        if r.status_code == 200:
            files = r.json().get('files', {})
            filename = list(files.keys())[0]
            content = files[filename].get('content', '{}')
            return json.loads(content)
    except: return {"bakiye": 1000, "portfoy": {}}

def save_full_data(data):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        filename = list(r.json()['files'].keys())[0] if r.status_code == 200 else "sazlik_cuzdan.json"
        payload = {"files": {filename: {"content": json.dumps(data, indent=4)}}}
        requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=payload)
    except: pass

# Skora göre dinamik yatırım tutarı (sazlik_live.py'den alındı)
def calculate_amount(score):
    if score >= 90: return 2000
    elif score >= 85: return 1750
    elif score >= 80: return 1500
    else: return 1000

# --- ARAYÜZ ---
st.title("🦅 SAZLIK PRO - GADDAR MOD")

full_data = get_full_data()
bakiye = full_data.get('bakiye', 1000.0)

tab1, tab2 = st.tabs(["🔍 Tavşan Avı (79+)", "📜 Z Raporu (Cüzdan)"])

# --- TAB 1: TAVŞAN AVI ---
with tab1:
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("🚀 TARAMAYI BAŞLAT", type="primary"):
            st.session_state.top_picks = news_bot.run_analysis_engine()

    if 'top_picks' in st.session_state:
        cols = st.columns(3)
        for i, stock in enumerate(st.session_state.top_picks):
            yatirim_tutari = calculate_amount(stock['Guven_Skoru'])
            color = "#00ff41" if stock['Guven_Skoru'] >= 85 else "#4da6ff"
            
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card" style="border-top-color: {color}">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="ticker-text">{stock['Hisse']}</span>
                        <span style="color:{color}; font-weight:bold;">Skor: {stock['Guven_Skoru']:.1f}</span>
                    </div>
                    <div style="color:#888; font-size:12px; margin: 8px 0;">🧠 {stock['AI_Notu']}</div>
                    <div style="font-family:monospace; display:grid; grid-template-columns: 1fr 1fr;">
                        <span>Fiyat: ${stock['Fiyat']:.2f}</span>
                        <span style="color:#00ff41">Hedef: ${stock['Hedef']:.2f}</span>
                        <span style="color:#ff4444">Stop: ${stock['Stop']:.2f}</span>
                        <span style="color:#fff">Yatırım: ${yatirim_tutari}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"AL: {stock['Hisse']}", key=f"buy_{stock['Hisse']}"):
                    if bakiye >= yatirim_tutari:
                        adet = round(yatirim_tutari / stock['Fiyat'], 4)
                        full_data['portfoy'][stock['Hisse']] = {
                            "adet": adet,
                            "maliyet": stock['Fiyat'],
                            "tarih": str(datetime.now().date()),
                            "puan": stock['Guven_Skoru']
                        }
                        full_data['bakiye'] -= yatirim_tutari
                        full_data['gecmis_islemler'].append({
                            "tarih": str(datetime.now().date()), "sembol": stock['Hisse'], "islem": "ALIS", "fiyat": stock['Fiyat'], "adet": adet
                        })
                        save_full_data(full_data)
                        st.toast(f"✅ {stock['Hisse']} Portföye Eklendi!", icon="🦅")
                        st.rerun()
                    else:
                        st.error("❌ Yetersiz Bakiye!")

# --- TAB 2: Z RAPORU (TABLO & RENK OTOMATİĞİ) ---
with tab2:
    st.subheader("📊 Canlı Portföy Analitik")
    portfolio = full_data.get('portfoy', {})
    
    if portfolio:
        t_invested, t_current = 0, 0
        display_data = []

        for ticker, info in portfolio.items():
            try:
                # Canlı fiyat çek
                curr_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
            except: curr_price = info['maliyet']
            
            shares = info['adet']
            cost = info['maliyet']
            val = curr_price * shares
            invested = cost * shares
            pnl = val - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0
            
            t_invested += invested
            t_current += val
            
            # Durum Sinyalleri
            status = ""
            if pnl_pct <= -3: status = "🚨 STOP"
            elif pnl_pct >= 5: status = "🔥 KÂR AL"
            
            display_data.append({
                "Hisse": ticker,
                "Tarih": info['tarih'],
                "Adet": f"x{shares}",
                "Maliyet": f"${cost:.2f}",
                "Güncel": f"${curr_price:.2f}",
                "PNL %": pnl_pct,
                "PNL $": pnl,
                "Sinyal": status
            })

        df = pd.DataFrame(display_data)

        # Tabloyu Renklendirme Fonksiyonu
        def style_pnl(row):
            styles = [''] * len(row)
            if row['PNL %'] >= 0:
                styles[df.columns.get_loc('PNL %')] = 'color: #00ff41; font-weight: bold'
                styles[df.columns.get_loc('PNL $')] = 'color: #00ff41; font-weight: bold'
            else:
                styles[df.columns.get_loc('PNL %')] = 'color: #ff4444; font-weight: bold'
                styles[df.columns.get_loc('PNL $')] = 'color: #ff4444; font-weight: bold'
            
            if "STOP" in str(row['Sinyal']):
                return ['background-color: rgba(255, 68, 68, 0.1)'] * len(row)
            if "KÂR AL" in str(row['Sinyal']):
                return ['background-color: rgba(0, 255, 65, 0.1)'] * len(row)
            return styles

        st.dataframe(df.style.apply(style_pnl, axis=1).format({
            "PNL %": "%{:.2f}",
            "PNL $": "${:.2f}"
        }), use_container_width=True, hide_index=True)
        
        # --- ÖZET METRİKLER ---
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Kasa Bakiye", f"${full_data['bakiye']:.2f}")
        m2.metric("Portföy Değeri", f"${t_current:.2f}", delta=f"{t_current-t_invested:.2f}$")
        m3.metric("TOPLAM SERVET", f"${full_data['bakiye'] + t_current:.2f}", 
                  delta=f"%{( (t_current-t_invested)/t_invested*100 if t_invested > 0 else 0):.2f}")

    else:
        st.info("Cüzdan boş. Tavşan avına başla!")