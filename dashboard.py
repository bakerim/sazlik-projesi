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

# Savaş Günlüğü için Hafıza
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 2. CSS TASARIMI (SENİN TASARIMIN) ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    div[data-testid="stMetric"] {
        background-color: #161b22; 
        border: 1px solid #30363d; 
        padding: 10px; 
        border-radius: 8px;
    }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        background-color: #0d1117;
    }
    .market-safe { color: #3fb950; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #238636; border-radius: 10px; background: rgba(35, 134, 54, 0.1); }
    .market-danger { color: #f85149; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #da3633; border-radius: 10px; background: rgba(218, 54, 51, 0.1); }
    .signal-buy { color: #3fb950; font-weight: bold; }
    .signal-sell { color: #f85149; font-weight: bold; }
    .signal-hold { color: #58a6ff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. SAZLIK STRATEJİ HARİTASI ---
# Hangi hissede hangi silahı kullanacağız?
STRATEGY_MAP = {
    # ROKETLER (SuperTrend)
    "NVDA": "SUPER_TREND", "META": "SUPER_TREND", "TSLA": "SUPER_TREND",
    "AVGO": "SUPER_TREND", "MSFT": "SUPER_TREND", "LLY": "SUPER_TREND",
    # KALELER (MACD)
    "KO": "MACD", "PG": "MACD", "JNJ": "MACD", "PEP": "MACD",
    "JPM": "MACD", "XOM": "MACD", "CVX": "MACD", "MCD": "MACD"
}

FULL_WATCHLIST = list(STRATEGY_MAP.keys())

# --- 4. MOTOR FONKSİYONLARI ---

def calculate_supertrend(df, period=10, multiplier=3):
    """SuperTrend Hesaplama Motoru"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    atr = ta.volatility.average_true_range(high, low, close, window=period)
    hl2 = (high + low) / 2
    basic_upperband = hl2 + (multiplier * atr)
    basic_lowerband = hl2 - (multiplier * atr)
    
    final_upperband = pd.Series(0.0, index=df.index)
    final_lowerband = pd.Series(0.0, index=df.index)
    supertrend = pd.Series(0.0, index=df.index) # 1: UP, -1: DOWN
    
    for i in range(1, len(df.index)):
        if basic_upperband.iloc[i] < final_upperband.iloc[i-1] or close.iloc[i-1] > final_upperband.iloc[i-1]:
            final_upperband.iloc[i] = basic_upperband.iloc[i]
        else:
            final_upperband.iloc[i] = final_upperband.iloc[i-1]
            
        if basic_lowerband.iloc[i] > final_lowerband.iloc[i-1] or close.iloc[i-1] < final_lowerband.iloc[i-1]:
            final_lowerband.iloc[i] = basic_lowerband.iloc[i]
        else:
            final_lowerband.iloc[i] = final_lowerband.iloc[i-1]
            
        if supertrend.iloc[i-1] == 1:
            if close.iloc[i] < final_lowerband.iloc[i]:
                supertrend.iloc[i] = -1
            else:
                supertrend.iloc[i] = 1
        else:
            if close.iloc[i] > final_upperband.iloc[i]:
                supertrend.iloc[i] = 1
            else:
                supertrend.iloc[i] = -1
    return supertrend

@st.cache_data(ttl=300)
def get_live_analysis():
    """Tüm listeyi tarayıp canlı sinyal üreten ana fonksiyon"""
    results = []
    
    # İlerleme çubuğu
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(FULL_WATCHLIST):
        try:
            strategy = STRATEGY_MAP.get(ticker, "MACD")
            df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
            
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            if df.empty or len(df) < 50: continue

            price = df['Close'].iloc[-1]
            signal = "NÖTR"
            trend = "YATAY"
            
            # --- STRATEJİ MOTORU ---
            if strategy == "MACD":
                macd = ta.trend.MACD(close=df['Close'])
                macdh = macd.macd()
                macds = macd.macd_signal()
                
                # Son durum
                if macdh.iloc[-1] > macds.iloc[-1]:
                    trend = "YÜKSELİŞ"
                    signal = "AL" if macdh.iloc[-2] <= macds.iloc[-2] else "TUT"
                else:
                    trend = "DÜŞÜŞ"
                    signal = "SAT" if macdh.iloc[-2] >= macds.iloc[-2] else "NAKİT"
            
            elif strategy == "SUPER_TREND":
                st_series = calculate_supertrend(df)
                
                if st_series.iloc[-1] == 1:
                    trend = "YÜKSELİŞ"
                    signal = "AL" if st_series.iloc[-2] == -1 else "TUT"
                else:
                    trend = "DÜŞÜŞ"
                    signal = "SAT" if st_series.iloc[-2] == 1 else "NAKİT"

            # RSI (Filtre Amaçlı)
            rsi = ta.momentum.rsi(df['Close'], window=14).iloc[-1]
            
            results.append({
                "Hisse": ticker,
                "Fiyat": price,
                "Strateji": strategy,
                "Trend": trend,
                "Sinyal": signal,
                "RSI": rsi,
                "Skor": 100 if signal == "AL" else (80 if signal == "TUT" else 20)
            })
            
        except Exception as e:
            print(f"Hata {ticker}: {e}")
        
        progress_bar.progress((i + 1) / len(FULL_WATCHLIST))
    
    progress_bar.empty()
    return pd.DataFrame(results)

# --- PİYASA ANALİZİ ---
def get_market_sentiment():
    try:
        spy = yf.download("SPY", period="6mo", interval="1d", progress=False, auto_adjust=True)
        if isinstance(spy.columns, pd.MultiIndex): spy.columns = spy.columns.droplevel(1)
        current = spy['Close'].iloc[-1]
        sma50 = spy['Close'].rolling(50).mean().iloc[-1]
        return "BOĞA" if current > sma50 else "AYI"
    except: return "NÖTR"

# --- PORTFÖY FONKSİYONLARI ---
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

# ==============================================================================
# ANA EKRAN (UI)
# ==============================================================================

st.title("🌾 Sazlık Pro V36.0: Grand Commander")
st.caption("Hibrit Motorlu Algoritmik Operasyon Merkezi")

# Piyasa Durumu
market = get_market_sentiment()
if "BOĞA" in market:
    st.markdown(f'<div class="market-safe">🟢 PİYASA: {market} (GÜVENLİ)</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="market-danger">🔴 PİYASA: {market} (RİSKLİ)</div>', unsafe_allow_html=True)

st.divider()

# Sekmeler
tab1, tab2, tab3, tab4 = st.tabs(["🤖 Robot Gözü", "🧪 Sniper Lab", "📒 Savaş Günlüğü", "🔎 Grafik Odası"])

# ------------------------------------------------------------------------------
# TAB 1: ROBOT GÖZÜ (Gözetleme Kulesi)
# ------------------------------------------------------------------------------
with tab1:
    col_btn, col_txt = st.columns([1, 4])
    scan_btn = col_btn.button("🚀 Piyasayı Tara", type="primary")
    
    if scan_btn or 'scan_results' not in st.session_state:
        if scan_btn:
            st.session_state.scan_results = get_live_analysis()
    
    if 'scan_results' in st.session_state:
        df_res = st.session_state.scan_results
        
        # KPI Kartları
        k1, k2, k3 = st.columns(3)
        al_sinyali = len(df_res[df_res['Sinyal'] == "AL"])
        sat_sinyali = len(df_res[df_res['Sinyal'] == "SAT"])
        k1.metric("Toplam Takip", len(df_res))
        k2.metric("AL Fırsatı", al_sinyali, delta_color="normal")
        k3.metric("SAT Uyarısı", sat_sinyali, delta_color="inverse")
        
        st.subheader("📋 Sinyal Tablosu")
        
        # Renklendirme Fonksiyonu
        def color_df(val):
            color = ''
            if val == 'AL' or val == 'YÜKSELİŞ': color = 'background-color: #1f7a1f; color: white'
            elif val == 'SAT' or val == 'DÜŞÜŞ': color = 'background-color: #990000; color: white'
            elif val == 'TUT': color = 'background-color: #004085; color: white'
            elif val == 'SUPER_TREND': color = 'color: orange'
            elif val == 'MACD': color = 'color: cyan'
            return color

        st.dataframe(
            df_res.style.map(color_df, subset=['Trend', 'Sinyal', 'Strateji']).format({"Fiyat": "${:.2f}", "RSI": "{:.1f}"}),
            use_container_width=True,
            height=500
        )
    else:
        st.info("Piyasa taraması için butona basınız.")

# ------------------------------------------------------------------------------
# TAB 2: SNIPER LAB (Detaylı Planlama)
# ------------------------------------------------------------------------------
with tab2:
    st.header("🧪 Sniper Elite: Operasyon Planlama")
    
    # Hangi hisseyi planlayacağız?
    if 'scan_results' in st.session_state:
        targets = st.session_state.scan_results['Hisse'].tolist()
    else:
        targets = FULL_WATCHLIST
        
    selected_target = st.selectbox("Hisse Seç", targets)
    
    # Bütçe Ayarı
    budget = st.number_input("Kasa ($)", value=250.0, step=10.0)
    
    if st.button("Analiz Et ve Planla"):
        # Seçilen hissenin verisini çek
        st.info(f"{selected_target} için strateji hesaplanıyor...")
        
        try:
            current_data = get_live_analysis()
            row = current_data[current_data['Hisse'] == selected_target].iloc[0]
            
            entry_price = row['Fiyat']
            signal = row['Sinyal']
            strategy = row['Strateji']
            
            # Sniper Kartı
            with st.container():
                st.markdown(f"### 🎯 Hedef: **{selected_target}**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Fiyat", f"${entry_price:.2f}")
                c2.metric("Strateji", f"{strategy}")
                
                if signal == "AL":
                    c3.markdown('<p class="signal-buy">SİNYAL: AL 🚀</p>', unsafe_allow_html=True)
                elif signal == "SAT":
                    c3.markdown('<p class="signal-sell">SİNYAL: SAT 🔻</p>', unsafe_allow_html=True)
                else:
                    c3.markdown(f'<p class="signal-hold">SİNYAL: {signal}</p>', unsafe_allow_html=True)

                st.divider()
                
                # PLANLAMA (Sadece AL veya TUT ise mantıklı)
                stop_loss = entry_price * 0.92 # %8 Stop
                target_1 = entry_price * 1.10
                target_2 = entry_price * 1.30
                
                st.write(f"**💰 Bütçe:** ${budget:.2f} -> **Adet:** {budget/entry_price:.2f}")
                
                col_p1, col_p2 = st.columns(2)
                col_p1.success(f"✅ Kar Al 1: ${target_1:.2f}")
                col_p2.error(f"🛑 Zarar Kes: ${stop_loss:.2f}")
                
                if st.button(f"➕ {selected_target} Günlüğe Ekle"):
                    add_to_portfolio(selected_target, entry_price, budget, target_1, stop_loss)
                    st.success("Operasyon günlüğe işlendi!")
                    
        except Exception as e:
            st.error("Lütfen önce 'Robot Gözü' sekmesinden tarama yapınız.")

# ------------------------------------------------------------------------------
# TAB 3: SAVAŞ GÜNLÜĞÜ (Portföy)
# ------------------------------------------------------------------------------
with tab3:
    st.header("📒 Aktif Operasyonlar")
    if len(st.session_state.portfolio) == 0: 
        st.info("📭 Günlük boş.")
    else:
        total_pl = 0
        for i, trade in enumerate(st.session_state.portfolio):
            try:
                # Anlık fiyatı çekmeye çalış, çok yavaşlarsa manuel güncelleme eklenebilir
                current_price = yf.Ticker(trade['Hisse']).history(period="1d")['Close'].iloc[-1]
            except: 
                current_price = trade['Giris_Fiyati']
            
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
                
                if c5.button("Kapat", key=f"del_{i}"):
                    st.session_state.portfolio.pop(i)
                    st.rerun()
                st.divider()
        
        st.metric("TOPLAM CANLI K/Z", f"${total_pl:.2f}")

# ------------------------------------------------------------------------------
# TAB 4: GRAFİK ODASI (Görsel Teyit)
# ------------------------------------------------------------------------------
with tab4:
    st.header("🔎 Grafik Odası")
    sel_ticker_chart = st.selectbox("Grafik Seç:", FULL_WATCHLIST, key="chart_select")
    
    if st.button("Grafiği Çiz"):
        with st.spinner("Çiziliyor..."):
            df_chart = yf.download(sel_ticker_chart, period="6mo", interval="1d", progress=False, auto_adjust=True)
            if isinstance(df_chart.columns, pd.MultiIndex): df_chart.columns = df_chart.columns.droplevel(1)
            
            # Stratejiye göre grafik
            strategy = STRATEGY_MAP.get(sel_ticker_chart, "MACD")
            
            fig = go.Figure()
            
            # Fiyat Mumları
            fig.add_trace(go.Candlestick(x=df_chart.index,
                            open=df_chart['Open'],
                            high=df_chart['High'],
                            low=df_chart['Low'],
                            close=df_chart['Close'],
                            name='Fiyat'))
            
            # İndikatör Çizimi
            if strategy == "SUPER_TREND":
                st_val = calculate_supertrend(df_chart)
                # Sadece görsel amaçlı basit çizim (trend değişimlerini okla gösterebiliriz ama şimdilik renkli çizgi yeterli)
                # SuperTrend'i görselleştirmek Plotly'de biraz karmaşıktır, basitçe SMA ekleyelim referans olsun
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'].rolling(10).mean(), line=dict(color='orange', width=1), name='EMA 10'))
                title_suffix = " - Strateji: SUPER TREND"
                
            else: # MACD
                macd = ta.trend.MACD(close=df_chart['Close'])
                fig.add_trace(go.Scatter(x=df_chart.index, y=macd.macd(), line=dict(color='blue', width=1), name='MACD', yaxis="y2"))
                fig.add_trace(go.Scatter(x=df_chart.index, y=macd.macd_signal(), line=dict(color='red', width=1), name='Sinyal', yaxis="y2"))
                title_suffix = " - Strateji: MACD"

            # Layout
            fig.update_layout(
                title=f"{sel_ticker_chart} {title_suffix}",
                template="plotly_dark",
                height=600,
                yaxis2=dict(title="MACD", overlaying="y", side="right") if strategy == "MACD" else None
            )
            
            st.plotly_chart(fig, use_container_width=True)
