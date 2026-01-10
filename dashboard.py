import streamlit as st
import pandas as pd
import json
import requests
import news_bot
from datetime import datetime
from config import GITHUB_TOKEN, GIST_ID

st.set_page_config(page_title="Sazlık Projesi", page_icon="🦅", layout="wide")

# --- CSS (V7.0 STİLİ) ---
st.markdown("""
<style>
    .card {
        background-color: #0e1117;
        border: 1px solid #30333d;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .card:hover { border-color: #00ff41; transform: scale(1.01); }
    
    .ticker-row { display: flex; justify_content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 8px; margin-bottom: 10px; }
    .ticker-name { font-size: 22px; font-weight: 900; color: #fff; }
    .score-badge { font-size: 16px; font-weight: bold; padding: 4px 10px; border-radius: 15px; color: #000; }
    
    .ai-row { font-size: 12px; color: #00ff41; font-style: italic; margin-bottom: 12px; border-left: 2px solid #00ff41; padding-left: 8px; }
    
    .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-size: 13px; font-family: 'Courier New'; color: #ccc; }
    .val-up { color: #00ff41; }
    .val-down { color: #ff4444; }
    .val-neut { color: #4da6ff; }
    
    .invest-row { margin-top: 12px; text-align: right; border-top: 1px solid #333; padding-top: 8px; }
    .invest-amount { font-size: 18px; font-weight: bold; color: #fff; }
</style>
""", unsafe_allow_html=True)

GIST_FILENAME = "sazlik_portfolio.json"

def get_portfolio():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        if r.status_code == 200:
            files = r.json().get('files', {})
            if files:
                content = files[list(files.keys())[0]].get('content', '{}')
                return json.loads(content) if content else {}
        return {}
    except: return {}

def save_portfolio(portfolio):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        filename = list(r.json()['files'].keys())[0] if r.status_code == 200 else "portfolio.json"
        data = {"files": {filename: {"content": json.dumps(portfolio, indent=4)}}}
        requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=data)
    except: pass

def create_card(stock, yatirim):
    if stock['Guven_Skoru'] >= 85: color = "#00ff41"
    elif stock['Guven_Skoru'] >= 70: color = "#4da6ff"
    else: color = "#ffbb00"
    
    html = f"""
    <div class="card" style="border-top: 3px solid {color};">
        <div class="ticker-row">
            <span class="ticker-name" style="color:{color}">{stock['Hisse']}</span>
            <span class="score-badge" style="background-color:{color}">{stock['Guven_Skoru']:.1f}</span>
        </div>
        <div class="ai-row">🤖 {stock['AI_Notu']}</div>
        <div class="metric-grid">
            <div>Fiyat: <span style="color:white">${stock['Fiyat']:.2f}</span></div>
            <div>Potansiyel: <span class="val-neut">%{stock['Pot_Kar']:.2f}</span></div>
            <div>Stop: <span class="val-down">${stock['Stop']:.2f}</span></div>
            <div>Hedef: <span class="val-up">${stock['Hedef']:.2f}</span></div>
        </div>
        <div class="invest-row">
            <span style="font-size:12px; color:#888">GİRİŞ TUTARI:</span>
            <span class="invest-amount">${yatirim}</span>
        </div>
    </div>
    """
    return html

st.title("🦅 SAZLIK - V7.0 GADDAR MOD")
st.caption("Filtre: Gaddar (SMA200 Altını Affetmez) | Puanlama: Bonkör (Fırsat Varsa 90+) | Tarama: Full")

col1, col2 = st.columns([1,3])
with col1:
    kasa = st.number_input("💵 Kasa ($)", value=1000.0, step=100.0)

tab1, tab2 = st.tabs(["🚀 Piyasa Taraması", "💼 Portföy"])

with tab1:
    if st.button("TARAMAYI BAŞLAT", type="primary"):
        with st.spinner("Gaddar Mod devrede... Zayıf halkalar eleniyor..."):
            results = news_bot.run_analysis_engine()
            results = sorted(results, key=lambda x: x['Guven_Skoru'], reverse=True)
            top_picks = results[:9] # İlk 9 taneyi göster
            
            if top_picks:
                current_portfolio = get_portfolio()
                st.success(f"🦁 {len(top_picks)} adet elit fırsat bulundu.")
                
                cols = st.columns(3)
                for i, stock in enumerate(top_picks):
                    # Bonkör Yatırım Hesabı
                    if stock['Guven_Skoru'] >= 85: ratio = 0.25
                    elif stock['Guven_Skoru'] >= 75: ratio = 0.20
                    else: ratio = 0.15
                    yatirim = round(kasa * ratio, 2)
                    
                    with cols[i%3]:
                        st.markdown(create_card(stock, yatirim), unsafe_allow_html=True)
                        key = f"btn_{stock['Hisse']}_{datetime.now().timestamp()}"
                        
                        if stock['Hisse'] in current_portfolio:
                            st.button(f"✅ Cüzdanda Var", key=key, disabled=True)
                        else:
                            if st.button(f"AL: {stock['Hisse']}", key=key):
                                adet = round(yatirim / stock['Fiyat'], 4)
                                current_portfolio[stock['Hisse']] = {
                                    "cost": stock['Fiyat'], "shares": adet,
                                    "date": str(datetime.now().date()),
                                    "total_invested": yatirim, "stop": stock['Stop'], "target": stock['Hedef']
                                }
                                save_portfolio(current_portfolio)
                                st.toast(f"{stock['Hisse']} eklendi!", icon="🦅")
            else:
                st.warning("Gaddar Mod: Piyasa çok kötü, kriterlere uyan sağlam kağıt yok.")

with tab2:
    st.header("📊 Portföy Z Raporu")
    portfolio = get_portfolio() # sazlik_cuzdan.json verisi
    
    if portfolio:
        # Terminal çıktısı gibi sade bir liste hazırlıyoruz
        report_data = []
        toplam_kar_zarar = 0
        
        for ticker, info in portfolio.items():
            # Güncel fiyatı çek (yfinance ile)
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
            except:
                current_price = info['cost'] # Hata olursa maliyeti yaz
            
            # Hesaplamalar
            total_value = current_price * info['shares']
            pnl = (current_price - info['cost']) * info['shares']
            pnl_perc = ((current_price - info['cost']) / info['cost']) * 100
            toplam_kar_zarar += pnl
            
            # Terminal stili satır oluşturma
            color = "🟢" if pnl >= 0 else "🔴"
            report_data.append({
                "Hisse": f"{color} {ticker}",
                "Fiyat (Güncel)": f"${current_price:.2f}",
                "Adet": f"x{info['shares']}",
                "Maliyet (Ort)": f"${info['cost']:.2f}",
                "Değer": f"${total_value:.0f}$",
                "PNL (%)": f"%{pnl_perc:.2f}",
                "PNL ($)": f"{'+' if pnl >= 0 else ''}{pnl:.1f}$"
            })
        
        # DataFrame olarak terminal tarzı gösterim
        df_portfolio = pd.DataFrame(report_data)
        st.table(df_portfolio) # st.table daha sade ve sabit bir görüntü sunar
        
        # Alt Toplam Paneli
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Nakit (Boşta)", f"${kasa:.2f}")
        with c2:
            hisse_degeri = sum([float(d['Değer'].replace('$','')) for d in report_data])
            st.metric("Hisse Değeri", f"${hisse_degeri:.2f}")
        with c3:
            toplam_servet = kasa + hisse_degeri
            st.metric("TOPLAM SERVET", f"${toplam_servet:.2f}", delta=f"{toplam_kar_zarar:.2f}$")
            
    else:
        st.info("Portföy henüz boş. Tavşan avına başla! 🦅")