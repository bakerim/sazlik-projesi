import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Pro - Komuta Merkezi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. KULLANICI SİSTEMİ ---
USERS = {
    "mert": "1317",
    "murat": "5199"
}

# --- 3. VERİ TABANI ---
def get_user_file(username):
    return f"portfolio_{username}.json"

def load_portfolio(username):
    filename = get_user_file(username)
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def save_portfolio(username, data):
    filename = get_user_file(username)
    with open(filename, "w") as f:
        json.dump(data, f)

# --- 4. YARDIMCI MOTORLAR ---
def get_historical_price(ticker, date_obj):
    start_date = date_obj
    end_date = date_obj + timedelta(days=5)
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if not df.empty: return df.iloc[0]['Close']
        return None
    except: return None

# --- 5. HESAPLAMA MOTORLARI ---
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

# --- 6. GİRİŞ EKRANI ---
def login_screen():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.container():
            st.markdown("<h1 style='text-align: center;'>🔐 Sazlık Pro</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #8b949e;'>Varlık Yönetim Sistemi</p>", unsafe_allow_html=True)
            
            user_input = st.text_input("Kullanıcı Adı")
            pass_input = st.text_input("Şifre", type="password")
            
            if st.button("Giriş Yap", use_container_width=True, type="primary"):
                if user_input in USERS and USERS[user_input] == pass_input:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user_input
                    st.session_state['portfolio'] = load_portfolio(user_input)
                    st.rerun()
                else:
                    st.error("Yetkisiz Erişim!")

# --- 7. ANA PANEL ---
def main_dashboard():
    # CSS
    st.markdown("""
    <style>
        .stApp { background-color: #0d1117; }
        div[data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 8px; }
        .market-safe { color: #3fb950; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #238636; border-radius: 10px; background: rgba(35, 134, 54, 0.1); }
        .market-danger { color: #f85149; font-weight: bold; font-size: 20px; text-align: center; padding: 10px; border: 1px solid #da3633; border-radius: 10px; background: rgba(218, 54, 51, 0.1); }
        .badge-stock { background-color: #1f6feb; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
        .badge-crypto { background-color: #d29922; color: black; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
        .badge-commodity { background-color: #8b949e; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

    c_user, c_logout = st.columns([8, 1])
    c_user.caption(f"👤 Yönetici: **{st.session_state['username'].upper()}**")
    if c_logout.button("Çıkış"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state['portfolio'] = []
        st.rerun()

    st.title("🌾 Komuta Merkezi V38.0")
    
    market = get_market_sentiment()
    if "BOĞA" in market: st.markdown(f'<div class="market-safe">🟢 PİYASA: {market} - GÜVENLİ</div>', unsafe_allow_html=True)
    else: st.markdown(f'<div class="market-danger">🔴 PİYASA: {market} - RİSKLİ</div>', unsafe_allow_html=True)
    
    df = load_market_data()
    st.divider()
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔭 Gözetleme", "🧪 Sniper Lab", "📒 BÜYÜK DEFTER", "🔎 Dedektif", "🗃️ Veri"])

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

    # ==========================================================================
    # TAB 2: SNIPER LAB (ROTA TASARIMI GERİ GELDİ & BUTON DÜZELDİ)
    # ==========================================================================
    with tab2:
        st.header("🧪 Sniper Elite: Otomatik Avlanma")
        col_in, col_inf = st.columns([1, 2])
        budget = col_in.number_input("Kasa ($)", value=250.0, step=10.0)
        trade_budget = budget * 0.98
        col_inf.success(f"**Savaş Bütçesi:** ${trade_budget:.2f}")

        if st.button("🚀 Piyasayı Tara", type="primary"):
            with st.spinner("Fırsatlar Taranıyor..."):
                opportunities = []
                for ticker in FULL_WATCHLIST:
                    res = analyze_sniper(ticker)
                    if res and res["Durum"] == "AL (SNIPER)":
                        opportunities.append(res)
                opportunities.sort(key=lambda x: x["RSI"], reverse=True)
                
                if not opportunities:
                    st.warning("💤 Atış menzilinde hedef yok.")
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
                        
                        # --- KART BAŞLANGICI ---
                        with st.container():
                            st.divider()
                            # Başlık
                            c_head1, c_head2 = st.columns([3, 1])
                            c_head1.markdown(f"### 🎯 HEDEF: **{ticker}**")
                            c_head2.metric("RSI Gücü", f"{plan['RSI']:.1f}")
                            
                            # Giriş Bilgileri
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Giriş Fiyatı", f"${entry:.2f}")
                            c2.metric("Yatırım", f"${trade_budget:.2f}")
                            c3.metric("Adet", f"{trade_budget/entry:.2f}")
                            
                            st.info(f"📄 **GÖREV EMRİ:** Parça Hisse ile **${trade_budget:.2f}** tutarında **{ticker}** al. Stop: ${stop_loss:.2f}")
                            
                            # --- 3 KADEMELİ SATIŞ ROTASI (RENKLİ KUTULARLA) ---
                            st.markdown("#### 📍 3 KADEMELİ SATIŞ ROTASI")
                            r1, r2, r3 = st.columns(3)
                            
                            with r1:
                                st.success(f"**1. GÜVENLİK**\n\n🎯 **${target_1:.2f}**")
                                st.caption("Pozisyonun %50'sini sat.")
                                st.markdown(f":green[**Kar: +${profit_1:.2f}**]")

                            with r2:
                                st.warning(f"**2. TREND**\n\n🎯 **${target_2:.2f}**")
                                st.caption("Kalanın %50'sini sat.")
                                st.markdown(f":green[**Kar: +${profit_2:.2f}**]")

                            with r3:
                                st.error(f"**3. JACKPOT**\n\n🎯 **${target_3:.2f}+**")
                                st.caption("Kalanı sür.")
                                st.markdown(f":green[**Kar: +${profit_3:.2f}+**]")
                            
                            st.markdown(f"### 💰 Tahmini Toplam Kar: :green[${total_potential_profit:.2f}]")

                            # --- DEFTERE İŞLEME BUTONU (DÜZELTİLDİ) ---
                            # Dictionary yapısı artık Tab 3 ile %100 uyumlu.
                            if st.button(f"➕ Deftere İşle", key=f"add_{ticker}"):
                                new_trade = {
                                    "Tip": "Hisse",
                                    "Hisse": ticker,
                                    "Giris_Tarihi": datetime.now().strftime("%Y-%m-%d"),
                                    "Giris_Fiyati": entry,
                                    "Yatirim": trade_budget,
                                    "Adet": trade_budget/entry,
                                    "Durum": "Acik",
                                    "Cikis_Tarihi": None,
                                    "Cikis_Fiyati": None
                                }
                                st.session_state.portfolio.append(new_trade)
                                save_portfolio(st.session_state['username'], st.session_state.portfolio)
                                st.success(f"✅ {ticker} başarıyla deftere işlendi! (Büyük Defter sekmesine bakabilirsin)")

    # TAB 3: BÜYÜK DEFTER
    with tab3:
        user = st.session_state['username']
        st.header(f"📒 {user.upper()} - Muhasebe Kayıtları")
        
        with st.expander("➕ Manuel İşlem / Geçmiş Kayıt Ekle", expanded=False):
            c_type, c_sym, c_amt = st.columns(3)
            i_type = c_type.selectbox("Varlık Tipi", ["Hisse", "Kripto", "Emtia"])
            i_sym = c_sym.text_input("Sembol (Örn: TSLA, BTC-USD, GC=F)").upper()
            i_amt = c_amt.number_input("Yatırım Tutarı ($)", min_value=1.0, value=100.0)
            
            c_date1, c_date2 = st.columns(2)
            i_buy_date = c_date1.date_input("Alış Tarihi")
            is_sold = c_date2.checkbox("Bu işlem satıldı mı (Kapalı)?")
            i_sell_date = None
            if is_sold: i_sell_date = c_date2.date_input("Satış Tarihi")
            
            if st.button("Kaydı Oluştur", type="primary"):
                if i_sym:
                    with st.spinner("Fiyatlar taranıyor..."):
                        buy_price = get_historical_price(i_sym, i_buy_date)
                        if buy_price:
                            qty = i_amt / buy_price
                            sell_price = None
                            status = "Acik"
                            if is_sold and i_sell_date:
                                sell_price = get_historical_price(i_sym, i_sell_date)
                                status = "Kapali"
                            
                            new_record = {
                                "Tip": i_type,
                                "Hisse": i_sym,
                                "Giris_Tarihi": i_buy_date.strftime("%Y-%m-%d"),
                                "Giris_Fiyati": buy_price,
                                "Yatirim": i_amt,
                                "Adet": qty,
                                "Durum": status,
                                "Cikis_Tarihi": i_sell_date.strftime("%Y-%m-%d") if i_sell_date else None,
                                "Cikis_Fiyati": sell_price
                            }
                            st.session_state.portfolio.append(new_record)
                            save_portfolio(user, st.session_state.portfolio)
                            st.success("✅ Kayıt oluşturuldu!")
                            st.rerun()
                        else: st.error("❌ Fiyat verisi bulunamadı.")

        st.divider()
        if len(st.session_state.portfolio) == 0: st.info("Defter boş.")
        else:
            total_active_value = 0
            total_realized_pl = 0
            for i, trade in enumerate(reversed(st.session_state.portfolio)):
                real_index = len(st.session_state.portfolio) - 1 - i
                badge_class = "badge-stock"
                if trade.get("Tip") == "Kripto": badge_class = "badge-crypto"
                elif trade.get("Tip") == "Emtia": badge_class = "badge-commodity"
                
                is_closed = trade.get("Durum") == "Kapali"
                if is_closed:
                    current_val = trade['Cikis_Fiyati'] * trade['Adet']
                    pl_val = current_val - trade['Yatirim']
                    pl_pct = (pl_val / trade['Yatirim']) * 100
                    total_realized_pl += pl_val
                else:
                    try:
                        live = yf.Ticker(trade['Hisse']).history(period="1d")
                        curr_price = live['Close'].iloc[-1]
                    except: curr_price = trade['Giris_Fiyati']
                    current_val = curr_price * trade['Adet']
                    pl_val = current_val - trade['Yatirim']
                    pl_pct = (pl_val / trade['Yatirim']) * 100
                    total_active_value += pl_val

                with st.container():
                    c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 2, 2, 2, 1])
                    c1.markdown(f"<span class='{badge_class}'>{trade.get('Tip', 'Hisse')}</span>", unsafe_allow_html=True)
                    c1.markdown(f"**{trade['Hisse']}**")
                    date_str = f"Alış: {trade['Giris_Tarihi']}"
                    if is_closed: date_str += f"<br>Satış: {trade['Cikis_Tarihi']}"
                    c2.markdown(date_str, unsafe_allow_html=True)
                    c3.write(f"Maliyet: ${trade['Giris_Fiyati']:.2f}")
                    c3.write(f"Yatırım: ${trade['Yatirim']:.2f}")
                    if is_closed:
                        c4.markdown("**KAPALI**")
                        c4.write(f"Satış: ${trade['Cikis_Fiyati']:.2f}")
                    else:
                        c4.markdown("**CANLI**")
                        c4.write(f"Fiyat: ${curr_price:.2f}")
                    color = "green" if pl_val >= 0 else "red"
                    c5.markdown(f":{color}[**${pl_val:.2f}**]")
                    c5.markdown(f":{color}[**%{pl_pct:.2f}**]")
                    if c6.button("Sil", key=f"del_{real_index}"):
                        st.session_state.portfolio.pop(real_index)
                        save_portfolio(user, st.session_state.portfolio)
                        st.rerun()
                    st.divider()

            st.markdown("### 📊 Muhasebe Özeti")
            m1, m2 = st.columns(2)
            m1.metric("Açık Pozisyon Kar/Zarar", f"${total_active_value:.2f}")
            m2.metric("Kasa Kar/Zarar (Gerçekleşen)", f"${total_realized_pl:.2f}")

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

# --- UYGULAMA BAŞLAT ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_screen()
