import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import json
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Pro - Komuta Merkezi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. KULLANICI SİSTEMİ VE AYARLAR ---
# Buraya istediğin kadar kullanıcı ekleyebilirsin.
# Şimdilik basit olması için şifreleri açık yazıyoruz.
USERS = {
    "mert": "1234",      # Senin Kullanıcı Adın ve Şifren
    "kardes": "5678"     # Kardeşinin Kullanıcı Adı ve Şifresi
}

# --- 3. VERİ TABANI FONKSİYONLARI (JSON KAYIT) ---
def get_user_file(username):
    return f"portfolio_{username}.json"

def load_portfolio(username):
    """Kullanıcının özel dosyasını okur."""
    filename = get_user_file(username)
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def save_portfolio(username, data):
    """Kullanıcının verilerini dosyaya yazar."""
    filename = get_user_file(username)
    with open(filename, "w") as f:
        json.dump(data, f)

# --- 4. CSS TASARIMI ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    div[data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 8px; }
    .market-safe { color: #3fb950; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #238636; border-radius: 10px; background: rgba(35, 134, 54, 0.1); }
    .market-danger { color: #f85149; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #da3633; border-radius: 10px; background: rgba(218, 54, 51, 0.1); }
    /* Login Kutusu */
    .login-box { border: 1px solid #30363d; padding: 40px; border-radius: 20px; background-color: #161b22; max-width: 400px; margin: auto; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 5. HESAPLAMA MOTORLARI (ORTAK) ---
FULL_WATCHLIST = ["NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "PLTR", "MSTR", "COIN"]

@st.cache_data(ttl=300)
def load_market_data():
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

def calculate_indicators(df):
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    return df

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

def analyze_sniper(ticker):
    try:
        df_sniper = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df_sniper.columns, pd.MultiIndex): df_sniper.columns = df_sniper.columns.get_level_values(0)
        if len(df_sniper) < 200: return None
        df_sniper = calculate_indicators(df_sniper)
        last_row = df_sniper.iloc[-1]
        durum = "BEKLE"
        if (last_row['Close'] > last_row['SMA_200'] and last_row['Close'] > last_row['SMA_50']) and (last_row['RSI_14'] >= 55) and (last_row['Close'] > last_row['SMA_20']):
            durum = "AL (SNIPER)"
        elif last_row['Close'] < last_row['SMA_50']: durum = "SAT"
        return { "Hisse": ticker, "Fiyat": last_row['Close'], "RSI": last_row['RSI_14'], "Durum": durum }
    except: return None

def get_chart_data(ticker):
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        return data
    except: return None

# --- 6. GİRİŞ EKRANI VE ANA UYGULAMA ---

def login_screen():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.container():
            st.markdown("<h1 style='text-align: center;'>🔐 Sazlık Pro</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #8b949e;'>Yetkili Personel Girişi</p>", unsafe_allow_html=True)
            
            user_input = st.text_input("Kullanıcı Adı")
            pass_input = st.text_input("Şifre", type="password")
            
            if st.button("Giriş Yap", use_container_width=True, type="primary"):
                if user_input in USERS and USERS[user_input] == pass_input:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user_input
                    # Giriş yapınca o kullanıcının portföyünü yükle
                    st.session_state['portfolio'] = load_portfolio(user_input)
                    st.rerun()
                else:
                    st.error("Hatalı kullanıcı adı veya şifre!")

def main_dashboard():
    # Üst Bar: Hoşgeldin ve Çıkış
    c_user, c_logout = st.columns([8, 1])
    c_user.caption(f"👤 Aktif Komutan: **{st.session_state['username'].upper()}**")
    if c_logout.button("Çıkış"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state['portfolio'] = []
        st.rerun()

    st.title("🌾 Komuta Merkezi V36.0")
    
    # PİYASA DURUMU
    market = get_market_sentiment()
    if "BOĞA" in market: st.markdown(f'<div class="market-safe">🟢 PİYASA: {market} - GÜVENLİ</div>', unsafe_allow_html=True)
    else: st.markdown(f'<div class="market-danger">🔴 PİYASA: {market} - RİSKLİ</div>', unsafe_allow_html=True)
    
    df = load_market_data()
    st.divider()
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔭 Gözetleme", "🧪 Sniper Lab", "📒 Günlük (Özel)", "🔎 Dedektif", "🗃️ Veri"])

    # TAB 1: GÖZETLEME
    with tab1:
        if not df.empty:
            st.subheader("🏆 Günün Yıldızları")
            top_picks = df.sort_values('Guven_Skoru_Num', ascending=False).head(3)
            cols = st.columns(3)
            for i, (index, row) in enumerate(top_picks.iterrows()):
                with cols[i]:
                    st.metric(label=f"#{i+1} {row['Hisse']}", value=f"${row['Fiyat']}", delta=f"Puan: {int(row['Guven_Skoru_Num'])}")
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            efsane = df[df['Guven_Skoru_Num'] >= 85]
            iyi = df[(df['Guven_Skoru_Num'] >= 70) & (df['Guven_Skoru_Num'] < 85)]
            orta = df[(df['Guven_Skoru_Num'] >= 50) & (df['Guven_Skoru_Num'] < 70)]
            
            c1.success(f"💎 Mükemmel ({len(efsane)})")
            if not efsane.empty: c1.write(", ".join(efsane['Hisse'].tolist()))
            c2.info(f"🚀 İyi ({len(iyi)})")
            if not iyi.empty: c2.write(", ".join(iyi['Hisse'].tolist()))
            c3.warning(f"⚖️ Orta ({len(orta)})")
            if not orta.empty: c3.write(", ".join(orta['Hisse'].tolist()))
        else: st.info("Veri havuzu boş.")

    # TAB 2: SNIPER LAB
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
                        target_1 = entry * 1.10
                        stop_loss = entry * 0.92
                        profit_1 = (trade_budget * 0.50) * 0.10
                        
                        with st.container():
                            st.divider()
                            c_head1, c_head2 = st.columns([3, 1])
                            c_head1.markdown(f"### 🎯 HEDEF: **{ticker}**")
                            c_head2.metric("RSI", f"{plan['RSI']:.1f}")
                            
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Giriş", f"${entry:.2f}")
                            c2.metric("Yatırım", f"${trade_budget:.2f}")
                            c3.metric("Adet", f"{trade_budget/entry:.2f}")
                            
                            st.info(f"📍 **ROTA:** Hedef: ${target_1:.2f} | Stop: ${stop_loss:.2f}")
                            
                            # Ekleme Butonu (Kişisel)
                            if st.button(f"➕ Benim Günlüğüme Ekle", key=f"add_{ticker}"):
                                new_trade = {
                                    "Hisse": ticker,
                                    "Giris_Fiyati": entry,
                                    "Yatirim": trade_budget,
                                    "Adet": trade_budget/entry,
                                    "Tarih": datetime.now().strftime("%Y-%m-%d")
                                }
                                st.session_state.portfolio.append(new_trade)
                                # DOSYAYA KAYDET
                                save_portfolio(st.session_state['username'], st.session_state.portfolio)
                                st.success(f"✅ {ticker} senin listene eklendi!")

    # TAB 3: GÜNLÜK (KİŞİSELLEŞTİRİLMİŞ)
    with tab3:
        user = st.session_state['username']
        st.header(f"📒 {user.upper()}'in Savaş Günlüğü")
        
        if len(st.session_state.portfolio) == 0: 
            st.info("Listen boş. 'Sniper Lab'dan işlem ekle.")
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
                    c1.markdown(f"**{trade['Hisse']}**")
                    c2.write(f"Giriş: ${trade['Giris_Fiyati']:.2f}")
                    c3.write(f"Anlık: **${current_price:.2f}**")
                    color = "green" if pl_usd >= 0 else "red"
                    c4.markdown(f":{color}[**${pl_usd:.2f} (%{pl_pct:.2f})**]")
                    if c5.button("Sil", key=f"del_{i}"):
                        st.session_state.portfolio.pop(i)
                        # SİLİNCE DE KAYDET
                        save_portfolio(st.session_state['username'], st.session_state.portfolio)
                        st.rerun()
                    st.divider()
            st.metric("PORTFÖY DURUMU", f"${total_pl:.2f}")

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

# --- 7. UYGULAMA AKIŞI ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_screen()
