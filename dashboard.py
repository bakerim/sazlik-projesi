import streamlit as st
import pandas as pd
import json
import requests
import news_bot
import yfinance as yf
from datetime import datetime
from config import GITHUB_TOKEN, GIST_ID

st.set_page_config(page_title="Sazlık Projesi", page_icon="🦅", layout="wide")

# --- CSS (Kartlar İçin Tasarım Korundu) ---
st.markdown("""
<style>
    .card { background-color: #0e1117; border: 1px solid #30333d; border-radius: 12px; padding: 16px; margin-bottom: 16px; border-top: 4px solid #4da6ff; }
    .ticker-text { font-size: 24px; font-weight: 900; color: #4da6ff; }
    .ai-section { background-color: rgba(77, 166, 255, 0.1); border-left: 3px solid #4da6ff; padding: 10px; font-size: 13px; color: #ccc; }
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

# --- ARAYÜZ ---
st.title("🦅 SAZLIK PRO - Z RAPORU")

full_data = get_full_data()
bakiye_gist = full_data.get('bakiye', 1000.0)

col_kasa, _ = st.columns([1, 3])
with col_kasa:
    kasa = st.number_input("💵 Kasa ($)", value=float(bakiye_gist), step=10.0)

tab1, tab2 = st.tabs(["🔍 Tavşan Avı (79+)", "📜 Z Raporu (Cüzdan)"])

# --- TAB 1: TAVŞAN AVI (KART TASARIMI KORUNDU) ---
with tab1:
    if st.button("🚀 TARAMAYI BAŞLAT", type="primary"):
        with st.spinner("Gemini 3 toplu analiz yapıyor..."):
            top_picks = news_bot.run_analysis_engine()
            if top_picks:
                st.success("🦁 Elit Finalistler Hazır!")
                cols = st.columns(3)
                for i, stock in enumerate(top_picks):
                    yatirim = round(kasa * (0.25 if stock['Guven_Skoru'] >= 85 else 0.20), 2)
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div class="card">
                            <div style="display:flex; justify-content:space-between;">
                                <span class="ticker-text">{stock['Hisse']}</span>
                                <span style="background:#4da6ff; color:#000; padding:2px 10px; border-radius:10px; font-weight:bold;">{stock['Guven_Skoru']:.1f}</span>
                            </div>
                            <div class="ai-section">🧠 {stock['AI_Notu']}</div>
                            <div style="font-family:monospace; font-size:12px; margin-top:10px;">
                                <b>Fiyat:</b> ${stock['Fiyat']:.2f} | <b>Hedef:</b> ${stock['Hedef']:.2f}
                            </div>
                            <div style="text-align:right; margin-top:10px; font-weight:bold; color:#fff;">Giriş: ${yatirim}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else: st.warning("79+ puanlı hisse bulunamadı.")

# --- TAB 2: Z RAPORU (TABLO MODUNA GEÇİLDİ - DİV HATASI BİTTİ) ---
with tab2:
    st.subheader("📊 Portföy Analitik Tablosu")
    portfolio_dict = full_data.get('portfoy', {})
    
    if portfolio_dict:
        rows = []
        t_invested, t_current = 0, 0
        
        with st.spinner("Piyasa verileri eşitleniyor..."):
            for ticker, info in portfolio_dict.items():
                # Yeni JSON hiyerarşisine göre verileri çek
                shares = info.get('adet', 0)
                cost = info.get('maliyet', 0)
                date = info.get('tarih', '---')
                
                # Yahoo Finance'ten anlık fiyat
                try:
                    ticker_obj = yf.Ticker(ticker)
                    curr_price = ticker_obj.history(period="1d")['Close'].iloc[-1]
                except: 
                    curr_price = cost
                
                invested = cost * shares
                current_val = curr_price * shares
                pnl = current_val - invested
                pnl_p = (pnl / invested * 100) if invested > 0 else 0
                
                t_invested += invested
                t_current += current_val
                
                # Tablo satırını oluştur
                rows.append({
                    "Hisse": ticker,
                    "Tarih": date,
                    "Adet": f"x{shares}",
                    "Maliyet": f"${cost:.2f}",
                    "Güncel": f"${curr_price:.2f}",
                    "Değer": f"${current_val:.2f}",
                    "PNL %": f"%{pnl_p:+.2f}",
                    "PNL $": f"${pnl:+.2f}"
                })
        
        # DataFrame oluştur ve bas
        df_p = pd.DataFrame(rows)
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        
        # --- ÖZET METRİKLER ---
        net_pnl = t_current - t_invested
        net_pnl_p = (net_pnl / t_invested * 100) if t_invested > 0 else 0
        
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Cüzdan Bakiye", f"${kasa:.2f}")
        m2.metric("Portföy Değeri", f"${t_current:.2f}", delta=f"{net_pnl:.2f}$")
        m3.metric("Toplam Servet", f"${kasa + t_current:.2f}", delta=f"%{net_pnl_p:.2f}")
        
        # Cezalılar ve Geçmiş (Genişletilebilir Alan)
        with st.expander("🕒 Cezalılar ve İşlem Geçmişi"):
            c1, c2 = st.columns(2)
            c1.write("🚫 Cezalı Hisseler")
            c1.json(full_data.get('cezalar', {}))
            c2.write("📜 Son İşlemler")
            c2.json(full_data.get('gecmis_islemler', [])[-5:]) # Son 5 işlem

    else: st.info("Portföy boş veya veriye ulaşılamadı.")