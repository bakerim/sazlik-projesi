import streamlit as st
import pandas as pd
import json
import requests
import news_bot
import yfinance as yf
from datetime import datetime
from config import GITHUB_TOKEN, GIST_ID

st.set_page_config(page_title="Sazlık Pro v2", page_icon="🦅", layout="wide")

# --- CSS: Terminal Ruhu ---
st.markdown("""
<style>
    .card { background-color: #0e1117; border: 1px solid #30333d; border-radius: 12px; padding: 15px; margin-bottom: 10px; border-top: 4px solid #4da6ff; }
    .ticker-text { font-size: 22px; font-weight: 900; color: #4da6ff; }
    .pnl-pos { color: #00ff41; font-weight: bold; }
    .pnl-neg { color: #ff4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- GIST MOTORU (OKUMA/YAZMA) ---
def get_full_data():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        if r.status_code == 200:
            files = r.json().get('files', {})
            filename = list(files.keys())[0]
            content = files[filename].get('content', '{}')
            return json.loads(content)
    except: return {"bakiye": 1000, "portfoy": {}, "gecmis_islemler": [], "cezalar": {}}

def save_full_data(data):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        filename = list(r.json()['files'].keys())[0] if r.status_code == 200 else "sazlik_cuzdan.json"
        payload = {"files": {filename: {"content": json.dumps(data, indent=4)}}}
        requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=payload)
    except: pass

# --- OTOMATİK İŞLEM MANTIĞI ---
def calculate_amount(score):
    if score >= 90: return 2000
    elif score >= 85: return 1750
    elif score >= 80: return 1500
    else: return 1000

# --- ARAYÜZ ---
st.title("🦅 SAZLIK PRO - Z RAPORU")

full_data = get_full_data()
bakiye = full_data.get('bakiye', 1000.0)

tab1, tab2 = st.tabs(["🔍 Tavşan Avı (79+)", "📜 Z Raporu (Cüzdan)"])

# --- TAB 1: ALIM MOTORU ---
with tab1:
    if st.button("🚀 TARAMAYI BAŞLAT", type="primary"):
        st.session_state.top_picks = news_bot.run_analysis_engine()

    if 'top_picks' in st.session_state:
        cols = st.columns(3)
        for i, stock in enumerate(st.session_state.top_picks):
            yatirim = calculate_amount(stock['Guven_Skoru'])
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card">
                    <span class="ticker-text">{stock['Hisse']}</span> | <b>Puan: {stock['Guven_Skoru']:.1f}</b><br>
                    <small>🧠 {stock['AI_Notu']}</small><br>
                    <b>Fiyat:</b> ${stock['Fiyat']:.2f} | <b>Yatırım:</b> ${yatirim}
                </div>
                """, unsafe_allow_html=True)
                
                # AL BUTONU
                if st.button(f"AL: {stock['Hisse']}", key=f"al_{stock['Hisse']}"):
                    if bakiye >= yatirim and stock['Hisse'] not in full_data['portfoy']:
                        adet = round(yatirim / stock['Fiyat'], 4)
                        full_data['portfoy'][stock['Hisse']] = {
                            "adet": adet, "maliyet": stock['Fiyat'], "tarih": str(datetime.now().date()), "puan": stock['Guven_Skoru']
                        }
                        full_data['bakiye'] -= yatirim
                        full_data['gecmis_islemler'].append({
                            "tarih": str(datetime.now().date()), "sembol": stock['Hisse'], "islem": "ALIS", "fiyat": stock['Fiyat'], "adet": adet
                        })
                        save_full_data(full_data)
                        st.rerun()

# --- TAB 2: Z RAPORU & OTOMATİK SATIŞ ---
with tab2:
    st.subheader("📊 Portföy Canlı Takip & Otomasyon")
    
    if st.button("🔄 TABLOYU GÜNCELLE VE KONTROL ET"):
        st.rerun()

    portfolio = full_data.get('portfoy', {})
    if portfolio:
        t_current = 0
        t_invested = 0
        rows = []

        for ticker, info in list(portfolio.items()):
            try:
                curr_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
            except: curr_price = info['maliyet']
            
            val = curr_price * info['adet']
            invested = info['maliyet'] * info['adet']
            pnl_pct = (curr_price - info['maliyet']) / info['maliyet'] * 100
            
            t_current += val
            t_invested += invested

            # --- OTOMATİK SATIŞ KONTROLÜ (-3 / +5) ---
            reason = ""
            if pnl_pct <= -3: reason = "ZARAR KES (STOP)"
            elif pnl_pct >= 5: reason = "KAR AL (TARGET)"

            if reason:
                # Otomatik Satış Kaydı
                full_data['bakiye'] += val
                full_data['gecmis_islemler'].append({
                    "tarih": str(datetime.now().date()), "sembol": ticker, "islem": "SATIS", 
                    "fiyat": curr_price, "adet": info['adet'], "sebep": reason
                })
                del full_data['portfoy'][ticker]
                save_full_data(full_data)
                st.toast(f"🚨 {ticker} OTOMATİK SATILDI: {reason}")
                continue # Satılanı listeye ekleme

            rows.append({
                "Hisse": ticker, "Tarih": info['tarih'], "Adet": info['adet'],
                "Maliyet": info['maliyet'], "Güncel": curr_price, "PNL%": pnl_pct, "Değer": val
            })

        if rows:
            df = pd.DataFrame(rows)
            # Renkli Tablo Sunumu
            def color_pnl(val):
                color = '#00ff41' if val >= 0 else '#ff4444'
                return f'color: {color}; font-weight: bold'

            st.table(df.style.applymap(color_pnl, subset=['PNL%', 'Değer']).format({"PNL%": "{:.2f}%", "Maliyet": "{:.2f}$", "Güncel": "{:.2f}$", "Değer": "{:.0f}$"}))

            # TEK TIKLA SATIŞ BUTONLARI
            st.write("---")
            st.write("🖱️ **Manuel Satış İşlemi:**")
            sell_cols = st.columns(len(rows))
            for i, row in enumerate(rows):
                if sell_cols[i].button(f"SATIŞ: {row['Hisse']}"):
                    ticker = row['Hisse']
                    full_data['bakiye'] += row['Değer']
                    full_data['gecmis_islemler'].append({
                        "tarih": str(datetime.now().date()), "sembol": ticker, "islem": "SATIS", "fiyat": row['Güncel'], "adet": row['Adet'], "sebep": "MANUEL"
                    })
                    del full_data['portfoy'][ticker]
                    save_full_data(full_data)
                    st.rerun()

        # ÖZET
        st.code(f"""
========================================
💰 Nakit Bakiye   : {full_data['bakiye']:.2f}$
🏦 Hisse Değeri   : {t_current:.2f}$
💎 TOPLAM SERVET  : {full_data['bakiye'] + t_current:.2f}$
🚀 Toplam PNL     : {t_current - t_invested:+.2f}$
========================================""")
    else:
        st.info("Portföy boş.")