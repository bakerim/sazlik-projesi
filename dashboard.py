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

# --- 2. CSS TASARIMI (Görsel Motor) ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    
    /* OPERASYON KARTI (ANA TASARIM) */
    .op-card {
        background: #161b22;
        border: 2px solid #238636; /* Neon Yeşil Çerçeve */
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 0 20px rgba(35, 134, 54, 0.2);
        position: relative;
    }
    
    .op-card-b {
        border-color: #30363d; /* Gri Çerçeve (Plan B) */
        opacity: 0.85;
        box-shadow: none;
    }

    /* BAŞLIK ALANI */
    .op-header {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #30363d; padding-bottom: 15px; margin-bottom: 20px;
    }
    .op-title { font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 1px; }
    .op-badge { 
        background-color: #238636; color: white; padding: 5px 12px; 
        border-radius: 20px; font-size: 14px; font-weight: bold; box-shadow: 0 0 10px #238636;
    }

    /* BİLGİ IZGARASI */
    .op-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
    .op-label { font-size: 11px; font-weight: bold; color: #8b949e; letter-spacing: 1px; text-transform: uppercase; }
    .op-value { font-size: 22px; font-weight: bold; color: #e6edf3; font-family: 'Courier New', monospace; }

    /* TALİMAT KUTUSU */
    .op-instruction {
        background-color: rgba(35, 134, 54, 0.1); 
        border-left: 4px solid #238636;
        padding: 15px; border-radius: 4px; margin-bottom: 20px;
        color: #e6edf3; font-size: 15px; line-height: 1.5;
    }
    .op-instruction-warning {
        background-color: rgba(218, 54, 51, 0.1);
        border-left: 4px solid #da3633;
    }

    /* ALT BAR (HEDEFLER) */
    .op-footer {
        display: flex; justify-content: space-between; 
        background: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d;
    }
    .target-green { color: #3fb950; font-size: 20px; font-weight: bold; }
    .stop-red { color: #f85149; font-size: 20px; font-weight: bold; }

    /* DİĞER STANDARTLAR */
    .detective-card { background-color: #161b22; border: 2px solid #58a6ff; border-radius: 15px; padding: 30px; text-align: center; }
    .text-green { color: #3fb950 !important; } .text-red { color: #f85149 !important; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
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
        required = ['Hisse', 'Fiyat', 'Karar', 'Guven_Skoru', 'Hedef_Fiyat', 'Stop_Loss', 'Vade', 'Analiz_Ozeti']
        for col in required:
            if col not in df.columns: df[col] = "-"
        df = df.sort_values('Tarih', ascending=False).drop_duplicates('Hisse')
        df['Guven_Skoru_Num'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(0)
        return df[df['Hisse'].isin(FULL_WATCHLIST)]
    except:
        return pd.DataFrame()

df = pd.DataFrame()
df = load_data()

def safe_val(val, prefix=""):
    try:
        if pd.isna(val) or str(val).lower() in ['nan', '0', '']: return '-'
        return f"{prefix}{val}"
    except: return '-'

# --- SNIPER BARON ANALİZ MOTORU ---
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
        trend_score = 1 if (close > sma200 and close > sma50) else 0
        momentum_score = 1 if rsi >= 55 else 0
        trigger = close > sma20
        
        if trend_score and momentum_score and trigger:
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
        hist.ta.sma(length=200, append=True)
        rsi = hist['RSI_14'].iloc[-1]
        sma200 = hist['SMA_200'].iloc[-1]
        score = 50
        if rsi < 30: score += 25
        elif rsi < 40: score += 10
        elif rsi > 70: score -= 20
        if curr_price > sma200: score += 15
        else: score -= 10
        karar = "BEKLE"
        if score >= 75: karar = "GÜÇLÜ AL"
        elif score >= 60: karar = "AL"
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

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 AI Vitrini", "📊 Portföy Analizi", "🧪 250$ Deney Labı", "🗃️ Veri Havuzu", "🔎 Hisse Dedektifi"
])

# --- DUMMY TABS (Eski kodlarını korumak için kısa tuttum, buraya eski kodlarını yapıştırabilirsin) ---
with tab1: st.info("Diğer sekmeler standart modda çalışıyor.")
with tab2: st.info("Portföy analizi standart modda.")
with tab4: st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True)

# ==============================================================================
# --- SEKME 3: SNIPER BARON LABORATUVARI (CYBERPUNK MODE) ---
# ==============================================================================
with tab3:
    st.markdown("## 🧪 250$ Deney Laboratuvarı")
    st.markdown("Matematiğe güven. Duyguyu bırak. Tetiği çek.")
    
    col_in, col_inf = st.columns([1, 2])
    budget = col_in.number_input("Kasa ($)", value=250.0, step=10.0)
    trade_budget = budget * 0.98
    col_inf.success(f"**Savaş Bütçesi:** ${trade_budget:.2f} (Kasanın %98'i)")

    if st.button("🚀 Piyasayı Tara ve Emri Ver", type="primary"):
        with st.spinner("Hedefler taranıyor..."):
            opportunities = []
            for ticker in FULL_WATCHLIST:
                res = analyze_sniper(ticker)
                if res and res["Durum"] == "AL (SNIPER)":
                    opportunities.append(res)
            
            opportunities.sort(key=lambda x: x["RSI"], reverse=True)
            
            if not opportunities:
                st.warning("### 💤 Pusuya Devam")
                st.write("Şu an hiçbir hisse atış menzilinde değil.")
            else:
                plan_a = opportunities[0]
                plan_b = opportunities[1] if len(opportunities) > 1 else None
                
                # --- HTML KART OLUŞTURUCU (GİZLİ SİLAH) ---
                def render_card(plan, title, is_plan_b=False):
                    css_class = "op-card-b" if is_plan_b else "op-card"
                    ticker = plan['Hisse']
                    price = plan['Fiyat']
                    rsi = plan['RSI']
                    
                    target = price * 1.10
                    stop = price * 0.92
                    
                    adet = int(trade_budget / price)
                    
                    # Talimat Mesajını Hazırla
                    if adet == 0:
                        warn_class = "op-instruction-warning"
                        msg = f"""
                        <b>⚠️ BÜTÇE YETERSİZ!</b><br>
                        Paran (${trade_budget:.2f}), 1 adet {ticker} almaya yetmiyor.<br>
                        👉 <b>Sadece Parça Hisse (Fractional) alabiliyorsan devam et.</b><br>
                        👉 Alamıyorsan bu planı atla.
                        """
                    else:
                        warn_class = "op-instruction"
                        msg = f"""
                        <b>✅ ALIM EMRİ:</b><br>
                        • <b>Tam Hisse:</b> {adet} Adet al.<br>
                        • <b>Parça Hisse:</b> ${trade_budget:.2f} tutarında al.
                        """

                    # HTML BLOK (DİV'LER BURADA GİZLİ)
                    html = f"""
                    <div class="{css_class}">
                        <div class="op-header">
                            <div class="op-title">{title}: {ticker}</div>
                            <div class="op-badge">RSI: {rsi:.1f}</div>
                        </div>
                        
                        <div class="op-grid">
                            <div>
                                <div class="op-label">GİRİŞ FİYATI</div>
                                <div class="op-value">${price:.2f}</div>
                            </div>
                            <div style="text-align:right;">
                                <div class="op-label">YATIRILACAK</div>
                                <div class="op-value">${trade_budget:.2f}</div>
                            </div>
                        </div>
                        
                        <div class="{warn_class}">
                            {msg}
                        </div>
                        
                        <div class="op-footer">
                            <div>
                                <div class="op-label">HEDEF 1 (KAR AL)</div>
                                <div class="target-green">${target:.2f}</div>
                                <div style="font-size:11px; color:#8b949e;">%10 Kar - Yarısını Sat</div>
                            </div>
                            <div style="text-align:right;">
                                <div class="op-label">STOP LOSS</div>
                                <div class="stop-red">${stop:.2f}</div>
                                <div style="font-size:11px; color:#8b949e;">%8 Zarar - Kaçış</div>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)

                # KARTLARI BAS
                st.markdown(f"### 🔥 TESPİT EDİLEN FIRSATLAR ({len(opportunities)} Adet)")
                render_card(plan_a, "PLAN A (ANA HEDEF)", is_plan_b=False)
                
                if plan_b:
                    st.markdown("👇 **Eğer Plan A bütçeni aşıyorsa:**")
                    render_card(plan_b, "PLAN B (YEDEK GÜÇ)", is_plan_b=True)
                elif plan_a and int(trade_budget / plan_a['Fiyat']) == 0:
                    st.warning("⚠️ Plan A bütçeni aşıyor ve başka alternatif yok.")

# --- SEKME 5: DEDEKTİF ---
with tab5:
    st.header("🔎 Hisse Dedektifi")
    sel = st.selectbox("Hisse Seç:", sorted(FULL_WATCHLIST))
    if st.button("Analiz Et"):
        with st.spinner("Bakılıyor..."):
            r = canli_analiz_yap(sel)
            if r:
                c1, c2 = st.columns(2)
                with c1:
                    score = int(r['Guven_Skoru_Num'])
                    clr = "#238636" if score >= 70 else "#da3633"
                    st.markdown(f"""<div class="detective-card"><h1 style='color:white'>{r['Hisse']}</h1><h2 style='color:{clr}; font-size:48px'>{score}</h2><p style='color:#888'>PUAN</p></div>""", unsafe_allow_html=True)
                with c2:
                    st.metric("Fiyat", f"${r['Fiyat']:.2f}")
                    st.metric("Hedef", f"${r['Hedef_Fiyat']:.2f}")
                    st.info(r['Analiz_Ozeti'])
            else: st.error("Hata.")
