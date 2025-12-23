import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import ta
import numpy as np
from datetime import datetime

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Pro - Komuta Merkezi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Savaş Günlüğü (Portföy) Hafızası
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 2. CSS TASARIMI (Sazlık Estetiği) ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    div[data-testid="stMetric"] {
        background-color: #161b22; 
        border: 1px solid #30363d; 
        padding: 10px; 
        border-radius: 8px;
    }
    .market-safe { color: #3fb950; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #238636; border-radius: 10px; background: rgba(35, 134, 54, 0.1); margin-bottom: 20px; }
    .market-danger { color: #f85149; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #da3633; border-radius: 10px; background: rgba(218, 54, 51, 0.1); margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
        color: #c9d1d9;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. STRATEJI VE IZLEME LISTESI ---
STRATEGY_MAP = {
    "NVDA": "SUPER_TREND", "META": "SUPER_TREND", "TSLA": "SUPER_TREND",
    "AVGO": "SUPER_TREND", "AMZN": "SUPER_TREND", "MSFT": "SUPER_TREND",
    "GOOGL": "SUPER_TREND", "KO": "MACD", "PG": "MACD", "JNJ": "MACD", 
    "PEP": "MACD", "JPM": "MACD", "XOM": "MACD", "COST": "SUPER_TREND"
}
FULL_WATCHLIST = sorted(list(STRATEGY_MAP.keys()))

# --- 4. ANALIZ MOTORU FONKSIYONLARI ---

def calculate_supertrend(df, period=10, multiplier=3):
    high, low, close = df['High'], df['Low'], df['Close']
    atr = ta.volatility.average_true_range(high, low, close, window=period)
    hl2 = (high + low) / 2
    basic_ub, basic_lb = hl2 + (multiplier * atr), hl2 - (multiplier * atr)
    final_ub, final_lb = pd.Series(0.0, index=df.index), pd.Series(0.0, index=df.index)
    st_dir = pd.Series(0.0, index=df.index)
    for i in range(1, len(df.index)):
        final_ub.iloc[i] = basic_ub.iloc[i] if basic_ub.iloc[i] < final_ub.iloc[i-1] or close.iloc[i-1] > final_ub.iloc[i-1] else final_ub.iloc[i-1]
        final_lb.iloc[i] = basic_lb.iloc[i] if basic_lb.iloc[i] > final_lb.iloc[i-1] or close.iloc[i-1] < final_lb.iloc[i-1] else final_lb.iloc[i-1]
        if st_dir.iloc[i-1] == 1:
            st_dir.iloc[i] = -1 if close.iloc[i] < final_lb.iloc[i] else 1
        else:
            st_dir.iloc[i] = 1 if close.iloc[i] > final_ub.iloc[i] else -1
    return st_dir

@st.cache_data(ttl=300)
def run_global_scan():
    results = []
    for ticker in FULL_WATCHLIST:
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            strategy = STRATEGY_MAP.get(ticker, "MACD")
            price = df['Close'].iloc[-1]
            rsi = ta.momentum.rsi(df['Close'], window=14).iloc[-1]
            
            if strategy == "MACD":
                m = ta.trend.MACD(close=df['Close'])
                trend = "YÜKSELİŞ" if m.macd().iloc[-1] > m.macd_signal().iloc[-1] else "DÜŞÜŞ"
                signal = "AL" if trend == "YÜKSELİŞ" and m.macd().iloc[-2] <= m.macd_signal().iloc[-2] else ("SAT" if trend == "DÜŞÜŞ" and m.macd().iloc[-2] >= m.macd_signal().iloc[-2] else ("TUT" if trend == "YÜKSELİŞ" else "NAKİT"))
            else:
                st_val = calculate_supertrend(df)
                trend = "YÜKSELİŞ" if st_val.iloc[-1] == 1 else "DÜŞÜŞ"
                signal = "AL" if trend == "YÜKSELİŞ" and st_val.iloc[-2] == -1 else ("SAT" if trend == "DÜŞÜŞ" and st_val.iloc[-2] == 1 else ("TUT" if trend == "YÜKSELİŞ" else "NAKİT"))
            
            results.append({"Hisse": ticker, "Fiyat": price, "Strateji": strategy, "Trend": trend, "Sinyal": signal, "RSI": rsi})
        except: continue
    return pd.DataFrame(results)

def get_market_sentiment():
    try:
        spy = yf.download("SPY", period="6mo", progress=False, auto_adjust=True)
        if isinstance(spy.columns, pd.MultiIndex): spy.columns = spy.columns.droplevel(1)
        return "BOĞA" if spy['Close'].iloc[-1] > spy['Close'].rolling(50).mean().iloc[-1] else "AYI"
    except: return "NÖTR"

# --- 5. ANA EKRAN TASARIMI ---
st.title("🌾 Sazlık Pro V36.0: Grand Commander")
sentiment = get_market_sentiment()
if sentiment == "BOĞA":
    st.markdown(f'<div class="market-safe">🟢 PİYASA DURUMU: {sentiment} (GÜVENLİ)</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="market-danger">🔴 PİYASA DURUMU: {sentiment} (RİSKLİ)</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔭 Gözetleme", "🧪 Sniper Lab", "📒 BÜYÜK DEFTER", "🔎 Dedektif", "🗃️ Veri"])

# --- TAB 1: GÖZETLEME ---
with tab1:
    if st.button("🚀 Radarı Çalıştır (Canlı Tarama)"):
        st.session_state.radar_results = run_global_scan()
    
    if 'radar_results' in st.session_state:
        res = st.session_state.radar_results
        k1, k2, k3 = st.columns(3)
        k1.metric("İzlenen", len(res))
        k2.metric("AL Sinyali", len(res[res['Sinyal'] == "AL"]))
        k3.metric("Trend Pozitif", len(res[res['Trend'] == "YÜKSELİŞ"]))
        
        def color_row(val):
            if val in ['AL', 'YÜKSELİŞ']: return 'color: #3fb950'
            if val in ['SAT', 'DÜŞÜŞ']: return 'color: #f85149'
            return ''
        st.dataframe(res.style.map(color_row, subset=['Trend', 'Sinyal']), use_container_width=True)
    else:
        st.info("Piyasayı taramak için butona basın.")

# --- TAB 2: SNIPER LAB ---
with tab2:
    st.subheader("🎯 Operasyon Planlama")
    if 'radar_results' in st.session_state:
        options = st.session_state.radar_results['Hisse'].tolist()
        pick = st.selectbox("Hedef Seç:", options)
        row = st.session_state.radar_results[st.session_state.radar_results['Hisse'] == pick].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Fiyat", f"${row['Fiyat']:.2f}")
        c2.metric("Sinyal", row['Sinyal'])
        c3.metric("RSI", f"{row['RSI']:.1f}")
        
        entry = row['Fiyat']
        budget = st.number_input("Yatırım ($)", value=250.0)
        st.write(f"**Plan:** Stop: ${entry*0.92:.2f} | Hedef: ${entry*1.15:.2f}")
        if st.button(f"➕ {pick} Deftere İşle"):
            st.session_state.portfolio.append({"Hisse": pick, "Giris": entry, "Adet": budget/entry, "Tarih": datetime.now().strftime("%Y-%m-%d")})
            st.success("Kaydedildi!")
    else:
        st.warning("Önce Gözetleme sekmesinde tarama yapın.")

# --- TAB 3: BÜYÜK DEFTER ---
with tab3:
    st.subheader("📒 Aktif Pozisyonlar")
    if not st.session_state.portfolio:
        st.write("Defter henüz boş.")
    else:
        for i, p in enumerate(st.session_state.portfolio):
            c1, c2, c3, c4 = st.columns([1,1,1,1])
            c1.write(f"**{p['Hisse']}** ({p['Tarih']})")
            c2.write(f"Giriş: ${p['Giris']:.2f}")
            if c4.button("Kapat", key=f"close_{i}"):
                st.session_state.portfolio.pop(i)
                st.rerun()
            st.divider()

# --- TAB 4: DEDEKTİF (GRAFİK) ---
with tab4:
    st.subheader("🔎 Teknik İnceleme")
    target = st.selectbox("Hisse:", FULL_WATCHLIST)
    if st.button("Grafiği Getir"):
        data = yf.download(target, period="6mo", progress=False, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.droplevel(1)
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Fiyat")])
        fig.update_layout(template="plotly_dark", title=f"{target} Teknik Görünüm", height=600)
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 5: VERİ ---
with tab5:
    if 'radar_results' in st.session_state:
        st.download_button("Raporu İndir (CSV)", st.session_state.radar_results.to_csv().encode('utf-8'), "sazlik_report.csv", "text/csv")
        st.dataframe(st.session_state.radar_results)
