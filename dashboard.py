import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Pro - Komuta Merkezi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Savaş Günlüğü için Hafıza
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 2. CSS TASARIMI ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    
    /* Metrik Kutuları */
    div[data-testid="stMetric"] {
        background-color: #161b22; 
        border: 1px solid #30363d; 
        padding: 10px; 
        border-radius: 8px;
    }
    
    /* Konteyner Çerçeveleri */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        background-color: #0d1117;
    }
    
    /* Piyasa Durumu */
    .market-safe { color: #3fb950; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #238636; border-radius: 10px; background: rgba(35, 134, 54, 0.1); }
    .market-danger { color: #f85149; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #da3633; border-radius: 10px; background: rgba(218, 54, 51, 0.1); }
</style>
""", unsafe_allow_html=True)

# --- İZLEME LİSTESİ ---
FULL_WATCHLIST = ["NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "PLTR", "MSTR", "COIN"]

# --- VERİ YÜKLEME ---
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv("sazlik_signals.csv", on_bad_lines='skip', engine='python')
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        required = ['Hisse', 'Fiyat', 'Karar', 'Guven_Skoru', 'Hedef_Fiyat', 'Stop_Loss', 'Vade', 'Analiz_Ozeti']
        for col in required:
            if col not in df.columns: df[col] = "-"
        df = df.sort_values('Tarih', ascending=False).drop_duplicates('Hisse')
        df['Guven_Skoru_Num'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(50)
        df = df[df['Hisse'].isin(FULL_WATCHLIST)]
        return df
    except: return pd.DataFrame()

df = load_data()

# --- ÖZEL MATEMATİK MOTORU (PANDAS_TA YOK!) ---
def calculate_indicators(df):
    # SMA Hesaplama
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    # RSI Hesaplama (Manuel)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    return df

# --- PİYASA ANALİZİ ---
def get_market_sentiment():
    try:
        spy = yf.download("SPY", period="6mo", interval="1d", progress=False)
        if isinstance(spy.columns, pd.MultiIndex): spy.columns = spy.columns.get_level_values(0)
        if len(spy) < 50: return "NÖTR"
        current = spy['Close'].iloc[-1]
        sma50 = spy['Close'].rolling(50).mean().iloc[-1]
        if current > sma50: return "BOĞA"
        return "AYI"
    except: return "VERİ YOK"

# --- SNIPER ANALİZİ ---
def analyze_sniper(ticker):
    try:
        df_sniper = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df_sniper.columns, pd.MultiIndex):
            df_sniper.columns = df_sniper.columns.get_level_values(0)
        
        if len(df_sniper) < 200: return None
        
        # Manuel Motoru Kullan
        df_sniper = calculate_indicators(df_sniper)
        
        last_row = df_sniper.iloc[-1]
        close = last_row['Close']
        sma20 = last_row['SMA_20']
        sma50 = last_row['SMA_50']
        sma200 = last_row['SMA_200']
        rsi = last_row['RSI_14']
        
        durum = "BEKLE"
        if (close > sma200 and close > sma50) and (rsi >= 55) and (close > sma20):
            durum = "AL (SNIPER)"
        elif close < sma50: 
            durum = "SAT"
        
        return { "Hisse": ticker, "Fiyat": close, "RSI": rsi, "Durum": durum }
    except: return None

# --- GRAFİK VERİSİ ---
def get_chart_data(ticker):
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        return data
    except: return None

# --- PORTFÖY EKLEME ---
def add_to_portfolio(ticker, entry_price, amount, target, stop):
    st.session_state.portfolio.append({
        "Hisse": ticker,
        "Giris_Fiyati": entry_price,
        "Yatirim": amount,
        "Adet": amount / entry_price,
        "Hedef": target,
        "Stop": stop,
        "Tarih": datetime.now().strftime("%Y-%m-%d")
    })

# --- ANA EKRAN ---
st.title("🌾 Sazlık Pro V35.0: Grand Commander")
st.caption("Tam Teşekküllü Borsa Operasyon Merkezi")

market = get_market_sentiment()
if "BOĞA" in market:
    st.markdown(f'<div class="market-safe">🟢 PİYASA: {market} - GÜVENLİ</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="market-danger">🔴 PİYASA: {market} - RİSKLİ</div>', unsafe_allow_html=True)

st.divider()
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔭 Gözetleme", "🧪 Sniper Lab", "📒 Günlük", "🔎 Dedektif", "🗃️ Veri"])

# TAB 1: GÖZETLEME
with tab1:
    if not df.empty:
        st.subheader("🏆 Günün Yıldızları")
        top_picks = df.sort_values('Guven_Skoru_Num', ascending=False).head(3)
        cols = st.columns(3)
        for i, (index, row) in enumerate(top_picks.iterrows()):
            with cols[i]:
                st.metric(label=f"#{i+1} {row['Hisse']}", value=f"${row['Fiyat']}", delta=f"Puan: {int(row['Guven_Skoru_Num'])}")
                st.info(f"🎯 Hedef: {row['Hedef_Fiyat']}")
        
        st.divider()
        st.subheader("📊 Genel Tarama")
        efsane = df[df['Guven_Skoru_Num'] >= 85]
        iyi = df[(df['Guven_Skoru_Num'] >= 70) & (df['Guven_Skoru_Num'] < 85)]
        orta = df[(df['Guven_Skoru_Num'] >= 50) & (df['Guven_Skoru_Num'] < 70)]
        
        c1, c2, c3 = st.columns(3)
        c1.success(f"💎 Mükemmel ({len(efsane)})")
        if not efsane.empty: c1.write(", ".join(efsane['Hisse'].tolist()))
        c2.info(f"🚀 İyi ({len(iyi)})")
        if not iyi.empty: c2.write(", ".join(iyi['Hisse'].tolist()))
        c3.warning(f"⚖️ Orta ({len(orta)})")
        if not orta.empty: c3.write(", ".join(orta['Hisse'].tolist()))
    else: st.info("Veri havuzu boş.")

# TAB 2: SNIPER LAB (NATIVE UI)
with tab2:
    st.header("🧪 Sniper Elite: Operasyon Planlama")
    col_in, col_inf = st.columns([1, 2])
    budget = col_in.number_input("Kasa ($)", value=250.0, step=10.0)
    trade_budget = budget * 0.98
    col_inf.success(f"**Savaş Bütçesi:** ${trade_budget:.2f}")

    if st.button("🚀 Piyasayı Tara", type="primary"):
        with st.spinner("Taranıyor..."):
            opportunities = []
            for ticker in FULL_WATCHLIST:
                res = analyze_sniper(ticker)
                if res and res["Durum"] == "AL (SNIPER)":
                    opportunities.append(res)
            opportunities.sort(key=lambda x: x["RSI"], reverse=True)
            
            if not opportunities:
                st.warning("💤 Uygun fırsat yok.")
            else:
                for plan in opportunities[:2]:
                    ticker = plan['Hisse']
                    entry = plan['Fiyat']
                    
                    # HESAPLAMALAR
                    target_1 = entry * 1.10
                    target_2 = entry * 1.30
                    target_3 = entry * 1.50
                    stop_loss = entry * 0.92
                    
                    profit_1 = (trade_budget * 0.50) * 0.10
                    profit_2 = (trade_budget * 0.25) * 0.30
                    profit_3 = (trade_budget * 0.25) * 0.50
                    total_potential_profit = profit_1 + profit_2 + profit_3

                    with st.container():
                        st.divider()
                        c_head1, c_head2 = st.columns([3, 1])
                        c_head1.markdown(f"### 🎯 HEDEF: **{ticker}**")
                        c_head2.metric("RSI Gücü", f"{plan['RSI']:.1f}")

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Giriş Fiyatı", f"${entry:.2f}")
                        c2.metric("Yatırım", f"${trade_budget:.2f}")
                        c3.metric("Adet", f"{trade_budget/entry:.2f}")

                        st.info(f"📄 **GÖREV EMRİ:**\n\nParça Hisse (Fractional) emri ile **${trade_budget:.2f}** tutarında **{ticker}** al.\n\n🛑 **Stop Loss:** ${stop_loss:.2f} (%8)")

                        st.markdown("#### 📍 3 KADEMELİ SATIŞ ROTASI")
                        r1, r2, r3 = st.columns(3)
                        with r1:
                            st.success(f"**1. GÜVENLİK**\n\n🎯 **${target_1:.2f}**")
                            st.caption("Yarısını Sat (1-3 Hafta)")
                            st.markdown(f":green[**Kar: +${profit_1:.2f}**]")
                        with r2:
                            st.warning(f"**2. TREND**\n\n🎯 **${target_2:.2f}**")
                            st.caption("%25 Sat (1-2 Ay)")
                            st.markdown(f":green[**Kar: +${profit_2:.2f}**]")
                        with r3:
                            st.error(f"**3. JACKPOT**\n\n🎯 **${target_3:.2f}+**")
                            st.caption("Kalanı Sür (3-6 Ay)")
                            st.markdown(f":green[**Kar: +${profit_3:.2f}+**]")

                        st.markdown(f"### 💰 Tahmini Toplam Kar: :green[${total_potential_profit:.2f}]")
                        
                        if st.button(f"➕ {ticker} Günlüğe Ekle", key=f"add_{ticker}"):
                            add_to_portfolio(ticker, entry, trade_budget, target_1, stop_loss)
                            st.success(f"✅ {ticker} Eklendi!")

# TAB 3: GÜNLÜK
with tab3:
    st.header("📒 Aktif Operasyonlar")
    if len(st.session_state.portfolio) == 0: 
        st.info("📭 Günlük boş.")
    else:
        total_pl = 0
        for i, trade in enumerate(st.session_state.portfolio):
            try:
                live_data = yf.Ticker(trade['Hisse']).history(period="1d")
                current_price = live_data['Close'].iloc[-1]
            except: current_price = trade['Giris_Fiyati']
            pl_usd = (current_price - trade['Giris_Fiyati']) * trade['Adet']
            pl_pct = ((current_price - trade['Giris_Fiyati']) / trade['Giris_Fiyati']) * 100
            total_pl += pl_usd
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                c1.markdown(f"### **{trade['Hisse']}**")
                c2.write(f"Giriş: ${trade['Giris_Fiyati']:.2f}")
                c3.write(f"Anlık: **${current_price:.2f}**")
                color = "green" if pl_usd >= 0 else "red"
                c4.markdown(f":{color}[**${pl_usd:.2f} (%{pl_pct:.2f})**]")
                if c5.button("Sat/Sil", key=f"del_{i}"):
                    st.session_state.portfolio.pop(i)
                    st.rerun()
                st.divider()
        st.metric("TOPLAM CANLI K/Z", f"${total_pl:.2f}")

# TAB 4: GRAFİK
with tab4:
    st.header("🔎 Grafik")
    sel_ticker = st.selectbox("Hisse:", sorted(FULL_WATCHLIST))
    if st.button("Grafik Getir"):
        with st.spinner("Yükleniyor..."):
            chart_data = get_chart_data(sel_ticker)
            if chart_data is not None:
                fig = go.Figure(data=[go.Candlestick(x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], low=chart_data['Low'], close=chart_data['Close'])])
                fig.update_layout(title=f"{sel_ticker}", template="plotly_dark", height=500)
                st.plotly_chart(fig, use_container_width=True)
            else: st.error("Veri yok.")

# TAB 5: VERİ
with tab5: st.dataframe(df, use_container_width=True)