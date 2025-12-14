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

# --- 2. CSS (Sadece Gerekli Olanlar) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 10px; border-radius: 8px; border: 1px solid #30363d; }
    .css-1r6slb0 { border: 1px solid #30363d; padding: 20px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- İZLEME LİSTESİ (ÖZEL TİM) ---
FULL_WATCHLIST = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "PLTR", "MSTR", "COIN"
]

# --- VERİ YÜKLEME ---
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv("sazlik_signals.csv", on_bad_lines='skip', engine='python')
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        
        required = ['Hisse', 'Fiyat', 'Karar', 'Guven_Skoru', 'Hedef_Fiyat', 'Stop_Loss', 
                    'Vade', 'Kasa_Yonetimi', 'Risk_Yuzdesi', 'Kazanc_Potansiyeli', 'Analiz_Ozeti']
        for col in required:
            if col not in df.columns: df[col] = "-"
            
        df = df.sort_values('Tarih', ascending=False).drop_duplicates('Hisse')
        df['Guven_Skoru_Num'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(0)
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
st.markdown("---")

# VERİ AYRIŞTIRMA
robot_picks = pd.DataFrame()
ai_picks = pd.DataFrame()
if not df.empty:
    df_filtered = df[df['Hisse'].isin(FULL_WATCHLIST)]
    if not df_filtered.empty:
        robot_picks = df_filtered[df_filtered['Analiz_Ozeti'].str.contains('GARANTİCİ BABA', na=False) | (df_filtered['Haber_Baslik'] == "Teknik Tarama (Haber Yok)")]
        ai_picks = df_filtered[~df_filtered.index.isin(robot_picks.index)]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 AI Vitrini", "📊 Portföy Analizi", "🧪 250$ Deney Labı", "🗃️ Veri Havuzu", "🔎 Hisse Dedektifi"
])

# --- TAB 1: AI VİTRİNİ ---
with tab1:
    if not ai_picks.empty:
        top_picks = ai_picks.sort_values('Guven_Skoru_Num', ascending=False).head(3)
        cols = st.columns(3)
        for i, (index, row) in enumerate(top_picks.iterrows()):
            with cols[i]:
                st.metric(label=f"#{i+1} {row['Hisse']}", value=f"${row['Fiyat']}", delta=f"Puan: {int(row['Guven_Skoru_Num'])}")
                st.write(f"**Hedef:** {row['Hedef_Fiyat']}")
                st.write(f"**Stop:** {row['Stop_Loss']}")
                st.info(row['Vade'])
    else:
        st.info("Uygun sinyal yok.")

# --- TAB 2: PORTFÖY ---
with tab2:
    if not df.empty:
        efsane = df[df['Guven_Skoru_Num'] >= 85]
        iyi = df[(df['Guven_Skoru_Num'] >= 70) & (df['Guven_Skoru_Num'] < 85)]
        c1, c2 = st.columns(2)
        with c1: 
            st.success(f"💎 Mükemmel ({len(efsane)})")
            st.table(efsane[['Hisse', 'Fiyat', 'Guven_Skoru']])
        with c2: 
            st.info(f"🚀 İyi ({len(iyi)})")
            st.table(iyi[['Hisse', 'Fiyat', 'Guven_Skoru']])
    else:
        st.warning("Veri yok.")

# ==============================================================================
# --- TAB 3: 250$ SNIPER LABORATUVARI (HTML KULLANMADAN - NATIVE UI) ---
# ==============================================================================
with tab3:
    st.header("🧪 250$ Deney Laboratuvarı")
    st.caption("Duyguları bırak, matematiği uygula.")
    
    col_in, col_inf = st.columns([1, 2])
    budget = col_in.number_input("Kasa ($)", value=250.0, step=10.0)
    trade_budget = budget * 0.98
    col_inf.success(f"**Savaş Bütçesi:** ${trade_budget:.2f} (Kasanın %98'i)")

    if st.button("🚀 Piyasayı Tara", type="primary"):
        with st.spinner("Hesaplanıyor..."):
            opportunities = []
            for ticker in FULL_WATCHLIST:
                res = analyze_sniper(ticker)
                if res and res["Durum"] == "AL (SNIPER)":
                    opportunities.append(res)
            
            opportunities.sort(key=lambda x: x["RSI"], reverse=True)
            
            if not opportunities:
                st.warning("💤 Uygun fırsat yok.")
            else:
                plan_a = opportunities[0]
                plan_b = opportunities[1] if len(opportunities) > 1 else None
                
                # --- OPERASYON KARTI FONKSİYONU (STREAMLIT NATIVE) ---
                def show_card(plan, title_prefix, color_stripe):
                    with st.container():
                        st.markdown(f"### {color_stripe} {title_prefix}: {plan['Hisse']}")
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Giriş Fiyatı", f"${plan['Fiyat']:.2f}")
                        c2.metric("RSI Gücü", f"{plan['RSI']:.1f}")
                        c3.metric("Yatırılacak", f"${trade_budget:.2f}")
                        
                        adet = int(trade_budget / plan['Fiyat'])
                        
                        # ALIM TALİMATI KUTUSU
                        with st.chat_message("assistant"):
                            if adet == 0:
                                st.error(f"⚠️ **DİKKAT:** Paran 1 adet almaya yetmiyor ({plan['Fiyat']:.2f} > {trade_budget:.2f}).")
                                st.write("👉 **Sadece 'Parça Hisse' (Fractional) alabiliyorsan devam et.**")
                            else:
                                st.write(f"✅ **TALİMAT:** Tam hisse alacaksan **{adet} Adet** al.")
                                st.write(f"ℹ️ Parça hisse alacaksan direkt **${trade_budget:.2f}** tutarında al.")

                        # HEDEF & STOP
                        hc1, hc2 = st.columns(2)
                        hc1.success(f"🎯 **KAR AL (%10):** ${plan['Fiyat']*1.10:.2f}")
                        hc2.error(f"🛑 **STOP (%8):** ${plan['Fiyat']*0.92:.2f}")
                        st.divider()

                # PLANLARI GÖSTER
                show_card(plan_a, "PLAN A (Ana Hedef)", "🔥")
                
                if plan_b:
                    st.info("👇 Eğer Plan A bütçeni aşıyorsa buna geç:")
                    show_card(plan_b, "PLAN B (Yedek)", "🛡️")
                elif plan_a and int(trade_budget / plan_a['Fiyat']) == 0:
                     st.warning("⚠️ Plan A bütçeni aşıyor ve başka alternatif yok.")

# --- TAB 4 & 5 (AYNI KALDI) ---
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
