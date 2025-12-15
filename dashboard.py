import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# --- 1. SAYFA AYARLARI VE SESSION STATE ---
st.set_page_config(
    page_title="Sazlık Pro - Komuta Merkezi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Savaş Günlüğü için Hafıza (Session State)
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 2. CSS TASARIMI ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    
    /* Metrik Kutularını Özelleştir */
    div[data-testid="stMetric"] {
        background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px;
    }
    /* PİYASA DURUMU KUTUSU */
    .market-box {
        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; font-weight: bold; font-size: 20px;
    }
    .market-safe { background-color: rgba(35, 134, 54, 0.2); border: 2px solid #238636; color: #3fb950; }
    .market-danger { background-color: rgba(218, 54, 51, 0.2); border: 2px solid #da3633; color: #f85149; }

    /* RENKLER */
    .text-green { color: #3fb950 !important; } 
    .text-red { color: #f85149 !important; }
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

# --- PİYASA ANALİZİ (SPY) ---
def get_market_sentiment():
    try:
        spy = yf.download("SPY", period="6mo", interval="1d", progress=False)
        if len(spy) < 50: return "NÖTR"
        
        # Multi-index düzeltmesi
        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)
            
        current = spy['Close'].iloc[-1]
        sma50 = spy['Close'].rolling(50).mean().iloc[-1]
        
        if current > sma50: return "BOĞA (GÜVENLİ)"
        return "AYI (RİSKLİ)"
    except: return "VERİ YOK"

# --- SNIPER ANALİZİ ---
def analyze_sniper(ticker):
    try:
        df_sniper = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df_sniper.columns, pd.MultiIndex):
            df_sniper.columns = df_sniper.columns.get_level_values(0)
        if len(df_sniper) < 200: return None
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

# --- CANLI ANALİZ VE GRAFİK ---
def get_chart_data(ticker):
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except: return None

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

# --- 4. ANA EKRAN ---
st.title("🌾 Sazlık Pro V30.0: Grand Commander")
st.caption("Tam Teşekküllü Borsa Operasyon Merkezi")

# PİYASA DURUMU (TRAFİK IŞIĞI)
market_status = get_market_sentiment()
if "BOĞA" in market_status:
    st.markdown(f'<div class="market-box market-safe">🟢 PİYASA DURUMU: {market_status} - ATEŞ SERBEST</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="market-box market-danger">🔴 PİYASA DURUMU: {market_status} - DİKKATLİ OL</div>', unsafe_allow_html=True)

# SEKMELER (YENİ YAPI)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔭 Gözetleme Kulesi", "🧪 Sniper Lab", "📒 Savaş Günlüğü", "🔎 Dedektif", "🗃️ Veri"
])

# ==============================================================================
# TAB 1: GÖZETLEME KULESİ (BİRLEŞTİRİLMİŞ)
# ==============================================================================
with tab1:
    if not df.empty:
        st.subheader("🏆 Günün Yıldızları (Top 3)")
        top_picks = df.sort_values('Guven_Skoru_Num', ascending=False).head(3)
        cols = st.columns(3)
        for i, (index, row) in enumerate(top_picks.iterrows()):
            with cols[i]:
                st.metric(label=f"#{i+1} {row['Hisse']}", value=f"${row['Fiyat']}", delta=f"Puan: {int(row['Guven_Skoru_Num'])}")
                st.info(f"🎯 Hedef: {row['Hedef_Fiyat']}")

        st.divider()
        st.subheader("📊 Genel Tarama Durumu")
        c1, c2, c3, c4 = st.columns(4)
        efsane = df[df['Guven_Skoru_Num'] >= 85]
        iyi = df[(df['Guven_Skoru_Num'] >= 70) & (df['Guven_Skoru_Num'] < 85)]
        orta = df[(df['Guven_Skoru_Num'] >= 50) & (df['Guven_Skoru_Num'] < 70)]
        cop = df[df['Guven_Skoru_Num'] < 50]
        
        c1.success(f"💎 Mükemmel: {len(efsane)}")
        if not efsane.empty: c1.table(efsane[['Hisse', 'Fiyat']])
        
        c2.info(f"🚀 İyi: {len(iyi)}")
        if not iyi.empty: c2.table(iyi[['Hisse', 'Fiyat']])
        
        c3.warning(f"⚖️ Orta: {len(orta)}")
        c4.error(f"⛔ Uzak Dur: {len(cop)}")
    else:
        st.info("Veri havuzu boş. Lütfen analizleri çalıştırın.")

# ==============================================================================
# TAB 2: SNIPER LAB (ENVANTERE EKLEME ÖZELLİĞİ)
# ==============================================================================
with tab2:
    st.header("🧪 Sniper Elite: Operasyon Planlama")
    col_in, col_inf = st.columns([1, 2])
    budget = col_in.number_input("Kasa ($)", value=250.0, step=10.0)
    trade_budget = budget * 0.98
    col_inf.success(f"**Savaş Bütçesi:** ${trade_budget:.2f}")

    if st.button("🚀 Piyasayı Tara ve Yol Haritasını Çıkar", type="primary"):
        with st.spinner("Hedefler taranıyor..."):
            opportunities = []
            for ticker in FULL_WATCHLIST:
                res = analyze_sniper(ticker)
                if res and res["Durum"] == "AL (SNIPER)":
                    opportunities.append(res)
            opportunities.sort(key=lambda x: x["RSI"], reverse=True)
            
            if not opportunities:
                st.warning("💤 Uygun fırsat yok.")
            else:
                for plan in opportunities[:2]: # İlk 2 fırsat
                    ticker = plan['Hisse']
                    entry = plan['Fiyat']
                    
                    with st.container():
                        st.divider()
                        c_title, c_act = st.columns([3, 1])
                        c_title.markdown(f"### HEDEF: **{ticker}** (RSI: {plan['RSI']:.1f})")
                        
                        # --- OPERASYON KARTI ---
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Giriş", f"${entry:.2f}")
                        c2.metric("Yatırım", f"${trade_budget:.2f}")
                        c3.metric("Adet (Tahmini)", f"{trade_budget/entry:.2f}")
                        
                        target_1 = entry * 1.10
                        stop_loss = entry * 0.92
                        
                        st.info(f"📍 **ROTA:** Hedef 1: ${target_1:.2f} (%10) | Stop: ${stop_loss:.2f} (%8)")
                        
                        # ENVANTERE EKLEME BUTONU
                        if c_act.button(f"➕ {ticker} Günlüğe Ekle", key=f"add_{ticker}"):
                            add_to_portfolio(ticker, entry, trade_budget, target_1, stop_loss)
                            st.success(f"✅ {ticker} Savaş Günlüğüne işlendi!")

# ==============================================================================
# TAB 3: SAVAŞ GÜNLÜĞÜ (PORTFÖY TAKİBİ)
# ==============================================================================
with tab3:
    st.header("📒 Savaş Günlüğü (Aktif Operasyonlar)")
    
    if len(st.session_state.portfolio) == 0:
        st.info("Henüz aktif bir operasyonun yok. 'Sniper Lab'dan işlem ekleyebilirsin.")
    else:
        # Portföy Tablosu Hazırla
        total_pl = 0
        
        for i, trade in enumerate(st.session_state.portfolio):
            # Canlı Fiyat Çek
            try:
                live_data = yf.Ticker(trade['Hisse']).history(period="1d")
                current_price = live_data['Close'].iloc[-1]
            except:
                current_price = trade['Giris_Fiyati'] # Hata olursa giriş fiyatını baz al
            
            # Kar/Zarar Hesapla
            pl_usd = (current_price - trade['Giris_Fiyati']) * trade['Adet']
            pl_pct = ((current_price - trade['Giris_Fiyati']) / trade['Giris_Fiyati']) * 100
            total_pl += pl_usd
            
            # Kart Görünümü
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                c1.markdown(f"**{trade['Hisse']}**")
                c2.write(f"Giriş: ${trade['Giris_Fiyati']:.2f}")
                c3.write(f"Anlık: **${current_price:.2f}**")
                
                # Renkli K/Z
                color = "green" if pl_usd >= 0 else "red"
                c4.markdown(f":{color}[**${pl_usd:.2f} (%{pl_pct:.2f})**]")
                
                if c5.button("🗑️ Sil", key=f"del_{i}"):
                    st.session_state.portfolio.pop(i)
                    st.rerun()
                st.divider()
        
        st.metric("TOPLAM KAR/ZARAR", f"${total_pl:.2f}")

# ==============================================================================
# TAB 4: DEDEKTİF (GRAFİK DESTEKLİ)
# ==============================================================================
with tab4:
    st.header("🔎 Hisse Dedektifi (Grafik Masası)")
    sel_ticker = st.selectbox("İncele:", sorted(FULL_WATCHLIST))
    
    if st.button("Detaylı Analiz"):
        with st.spinner("Uydu görüntüleri alınıyor..."):
            chart_data = get_chart_data(sel_ticker)
            if chart_data is not None:
                # 1. Metrikler
                curr = chart_data['Close'].iloc[-1]
                prev = chart_data['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100
                
                m1, m2 = st.columns(2)
                m1.metric(f"{sel_ticker} Fiyat", f"${curr:.2f}", f"{pct:.2f}%")
                
                # 2. Grafik (Plotly)
                fig = go.Figure(data=[go.Candlestick(x=chart_data.index,
                                open=chart_data['Open'],
                                high=chart_data['High'],
                                low=chart_data['Low'],
                                close=chart_data['Close'])])
                fig.update_layout(title=f"{sel_ticker} - Son 3 Ay", template="plotly_dark", height=500)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error("Veri alınamadı.")

# ==============================================================================
# TAB 5: VERİ HAVUZU
# ==============================================================================
with tab5:
    st.dataframe(df, use_container_width=True)
