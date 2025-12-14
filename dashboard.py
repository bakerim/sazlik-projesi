import streamlit as st
import pandas as pd
import altair as alt
import yfinance as yf
import pandas_ta as ta

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Pro - Komuta Merkezi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS (Sadece Renk ve Kutu Stilleri İçin - HTML Yapısı Yok) ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    
    /* Metrik Kutuları */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
    }
    
    /* Başarı Mesajları (Yeşil) */
    .stSuccess {
        background-color: rgba(35, 134, 54, 0.1);
        border-left: 5px solid #238636;
    }
    
    /* Hata Mesajları (Kırmızı) */
    .stError {
        background-color: rgba(218, 54, 51, 0.1);
        border-left: 5px solid #da3633;
    }
    
    /* Bilgi Mesajları (Mavi) */
    .stInfo {
        background-color: rgba(56, 139, 253, 0.1);
        border-left: 5px solid #1f6feb;
    }
    
    /* Konteyner Çerçeveleri */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        background-color: #161b22;
    }
</style>
""", unsafe_allow_html=True)

# --- İZLEME LİSTESİ ---
FULL_WATCHLIST = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "PLTR", "MSTR", "COIN"
]

# --- VERİ YÜKLEME ---
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv("sazlik_signals.csv", on_bad_lines='skip', engine='python')
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        required = ['Hisse', 'Fiyat', 'Karar', 'Guven_Skoru', 'Hedef_Fiyat', 'Stop_Loss', 'Vade', 'Analiz_Ozeti', 'Kazanc_Potansiyeli', 'Risk_Yuzdesi']
        for col in required:
            if col not in df.columns: df[col] = "-"
        df = df.sort_values('Tarih', ascending=False).drop_duplicates('Hisse')
        df['Guven_Skoru_Num'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(50)
        df = df[df['Hisse'].isin(FULL_WATCHLIST)]
        return df
    except:
        return pd.DataFrame()

df = pd.DataFrame()
df = load_data()

# --- ANALİZ MOTORU ---
def analyze_sniper(ticker):
    try:
        df_sniper = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df_sniper.columns, pd.MultiIndex):
            df_sniper.columns = df_sniper.columns.get_level_values(0)
        
        if len(df_sniper) < 200: return None
        
        df_sniper.ta.rsi(length=14, append=True)
        df_sniper.ta.sma(length=20, append=True)
        df_sniper.ta.sma(length=50, append=True)
        df_sniper.ta.sma(length=200, append=True)
        
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

# --- CANLI ANALİZ ---
def canli_analiz_yap(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if len(hist) < 200: return None
        curr_price = hist['Close'].iloc[-1]
        hist.ta.rsi(length=14, append=True)
        rsi = hist['RSI_14'].iloc[-1]
        score = 50
        if rsi < 30: score += 25
        elif rsi < 40: score += 10
        elif rsi > 70: score -= 20
        karar = "BEKLE"
        if score >= 60: karar = "AL"
        elif score <= 30: karar = "SAT"
        return {
            'Hisse': ticker, 'Fiyat': curr_price, 'Karar': karar, 'Guven_Skoru_Num': score,
            'Hedef_Fiyat': curr_price * 1.05, 'Stop_Loss': curr_price * 0.95,
            'Vade': "1-2 Hafta", 'Analiz_Ozeti': f"RSI: {rsi:.1f}"
        }
    except: return None

# --- 4. ANA EKRAN ---
st.title("🌾 Sazlık Pro: Komuta Merkezi")
st.markdown(f"**Aktif Özel Tim:** `{', '.join(FULL_WATCHLIST)}`")
st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 AI Vitrini", "📊 Portföy Analizi", "🧪 250$ Deney Labı", "🗃️ Veri Havuzu", "🔎 Hisse Dedektifi"
])

# --- TAB 1: AI VİTRİNİ ---
with tab1:
    if not df.empty:
        top_picks = df.sort_values('Guven_Skoru_Num', ascending=False).head(3)
        cols = st.columns(3)
        for i, (index, row) in enumerate(top_picks.iterrows()):
            with cols[i]:
                st.subheader(f"#{i+1} {row['Hisse']}")
                st.metric(label="Fiyat", value=f"${row['Fiyat']}", delta=f"Puan: {int(row['Guven_Skoru_Num'])}")
                st.info(f"**Hedef:** {row['Hedef_Fiyat']} | **Stop:** {row['Stop_Loss']}")
    else:
        st.info("Veri havuzu boş.")

# --- TAB 2: PORTFÖY ANALİZİ ---
with tab2:
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.success("💎 **MÜKEMMEL FIRSATLAR**")
            st.dataframe(df[df['Guven_Skoru_Num'] >= 85][['Hisse', 'Fiyat', 'Guven_Skoru']], use_container_width=True)
        with c2:
            st.info("🚀 **İYİ FIRSATLAR**")
            st.dataframe(df[(df['Guven_Skoru_Num'] >= 70) & (df['Guven_Skoru_Num'] < 85)][['Hisse', 'Fiyat', 'Guven_Skoru']], use_container_width=True)
    else:
        st.warning("Veri bekleniyor.")

# ==============================================================================
# --- TAB 3: SNIPER ELITE LABORATUVARI (NATIVE UI - HTML YOK) ---
# ==============================================================================
with tab3:
    st.header("🧪 250$ Deney Laboratuvarı: SNIPER ELITE")
    
    col_in, col_inf = st.columns([1, 2])
    budget = col_in.number_input("Kasa ($)", value=250.0, step=10.0)
    trade_budget = budget * 0.98
    col_inf.success(f"**Savaş Bütçesi:** ${trade_budget:.2f} (Parça Hisse Alımı Aktif)")

    if st.button("🚀 Piyasayı Tara ve Yol Haritasını Çıkar", type="primary"):
        with st.spinner("Strateji hesaplanıyor..."):
            opportunities = []
            for ticker in FULL_WATCHLIST:
                res = analyze_sniper(ticker)
                if res and res["Durum"] == "AL (SNIPER)":
                    opportunities.append(res)
            
            opportunities.sort(key=lambda x: x["RSI"], reverse=True)
            
            if not opportunities:
                st.warning("### 💤 Pusuya Devam")
                st.write("Şu an atış menzilinde uygun hisse yok.")
            else:
                plan_a = opportunities[0]
                plan_b = opportunities[1] if len(opportunities) > 1 else None
                
                # --- OPERASYON KARTI (NATIVE STREAMLIT) ---
                def render_native_card(plan, label):
                    ticker = plan['Hisse']
                    entry_price = plan['Fiyat']
                    rsi = plan['RSI']
                    
                    target_1 = entry_price * 1.10
                    target_2 = entry_price * 1.30
                    target_3 = entry_price * 1.50
                    stop_loss = entry_price * 0.92
                    
                    profit_1 = (trade_budget * 0.50) * 0.10
                    profit_2 = (trade_budget * 0.25) * 0.30
                    profit_3 = (trade_budget * 0.25) * 0.50
                    total_potential_profit = profit_1 + profit_2 + profit_3

                    # KART BAŞLANGICI
                    with st.container():
                        st.divider()
                        c_title, c_rsi = st.columns([3, 1])
                        c_title.markdown(f"### {label}: **{ticker}**")
                        c_rsi.metric("RSI Gücü", f"{rsi:.1f}")
                        
                        # GİRİŞ BİLGİLERİ
                        c1, c2 = st.columns(2)
                        c1.metric("Giriş Fiyatı", f"${entry_price:.2f}")
                        c2.metric("Yatırılacak Tutar", f"${trade_budget:.2f}")
                        
                        # ALIM EMRİ KUTUSU
                        st.info(f"📄 **GÖREV EMRİ:**\n\nParça Hisse (Fractional) emri ile **${trade_budget:.2f}** tutarında **{ticker}** al.\n\n🛑 **Stop Loss:** ${stop_loss:.2f} (%8)")
                        
                        st.markdown("#### 📍 3 KADEMELİ SATIŞ ROTASI")
                        
                        # YOL HARİTASI (3 KOLON)
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.success(f"**1. GÜVENLİK KİLİDİ**\n\n🎯 **${target_1:.2f}**\n\nElindekinin **%50'sini** sat.\n\n💰 Kazanç: +${profit_1:.2f}")
                            st.caption("Tahmini: 1-3 Hafta")
                            
                        with col2:
                            st.success(f"**2. TREND KAZANCI**\n\n🎯 **${target_2:.2f}**\n\nElindekinin **%25'ini** sat.\n\n💰 Kazanç: +${profit_2:.2f}")
                            st.caption("Tahmini: 1-2 Ay")
                            
                        with col3:
                            st.success(f"**3. JACKPOT**\n\n🎯 **${target_3:.2f}+**\n\nKalan **%25'i** sür.\n\n💰 Kazanç: +${profit_3:.2f}+")
                            st.caption("Tahmini: 3-6 Ay")
                        
                        st.markdown(f"🎯 **Operasyon Başarılı Olursa Toplam Tahmini Kar: :green[${total_potential_profit:.2f}]**")

                st.subheader(f"🔥 TESPİT EDİLEN FIRSATLAR ({len(opportunities)} Adet)")
                render_native_card(plan_a, "PLAN A")
                
                if plan_b:
                    st.markdown("👇 **Alternatif:**")
                    render_native_card(plan_b, "PLAN B")

# --- TAB 4 & 5 ---
with tab4:
    st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True)
with tab5:
    st.header("🔎 Hisse Dedektifi")
    sel = st.selectbox("Hisse Seç:", sorted(FULL_WATCHLIST))
    if st.button("Analiz Et"):
        with st.spinner("Bakılıyor..."):
            r = canli_analiz_yap(sel)
            if r:
                c1, c2 = st.columns(2)
                c1.metric("Fiyat", f"${r['Fiyat']:.2f}")
                c1.metric("Puan", f"{int(r['Guven_Skoru_Num'])}")
                c2.info(r['Analiz_Ozeti'])
                st.success(f"Karar: {r['Karar']}")
            else: st.error("Hata.")
