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

# --- 2. CSS TASARIMI (TÜM MODÜLLER İÇİN) ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    
    /* TAB 1: VİTRİN KARTI */
    .top-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }
    .top-symbol { font-size: 36px; font-weight: 900; color: #ffffff; margin: 5px 0; }
    .top-price { font-size: 24px; font-weight: bold; color: #e6edf3; margin-bottom: 5px; }
    .top-vade { font-size: 14px; color: #8b949e; margin-bottom: 15px; font-style: italic; }
    .top-score { font-size: 20px; font-weight:bold; }
    
    /* TAB 2: İNFOGRAFİK KUTULARI */
    .info-box {
        padding: 15px; border-radius: 10px; text-align: center; color: white; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1);
    }
    .info-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
    .info-count { font-size: 42px; font-weight: 900; }
    .info-desc { font-size: 12px; opacity: 0.8; }
    
    .bg-legend { background: linear-gradient(135deg, #1a7f37 0%, #2da44e 100%); } 
    .bg-good { background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%); }   
    .bg-mid { background: linear-gradient(135deg, #9e6a03 0%, #d29922 100%); }     
    .bg-bad { background: linear-gradient(135deg, #da3633 0%, #f85149 100%); }     

    .stock-item {
        background-color: rgba(0,0,0,0.2); padding: 8px; margin: 5px 0; border-radius: 5px; display: flex; justify-content: space-between; font-size: 14px;
    }

    /* TAB 3: OPERASYON KARTI (YENİ TASARIM) */
    .op-card {
        background: #161b22;
        border: 2px solid #238636; /* Yeşil Çerçeve */
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 0 15px rgba(35, 134, 54, 0.2);
    }
    .op-card-b {
        background: #161b22;
        border: 2px solid #30363d; /* Gri Çerçeve */
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        opacity: 0.9;
    }
    .op-header {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #30363d; padding-bottom: 15px; margin-bottom: 20px;
    }
    .op-title { font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 1px; }
    .op-badge { 
        background-color: #238636; color: white; padding: 5px 12px; 
        border-radius: 20px; font-size: 14px; font-weight: bold;
    }
    .op-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
    .op-label { font-size: 11px; font-weight: bold; color: #8b949e; letter-spacing: 1px; text-transform: uppercase; }
    .op-value { font-size: 22px; font-weight: bold; color: #e6edf3; font-family: 'Courier New', monospace; }

    /* TALİMAT KUTUSU */
    .op-instruction {
        background-color: rgba(35, 134, 54, 0.15); 
        border-left: 4px solid #238636;
        padding: 15px; border-radius: 4px; margin-bottom: 20px;
        color: #e6edf3; font-size: 15px; line-height: 1.5;
    }
    .op-instruction-warning {
        background-color: rgba(218, 54, 51, 0.15);
        border-left: 4px solid #da3633;
        padding: 15px; border-radius: 4px; margin-bottom: 20px;
        color: #e6edf3; font-size: 15px; line-height: 1.5;
    }

    /* ALT BAR */
    .op-footer {
        display: flex; justify-content: space-between; 
        background: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d;
    }
    .target-green { color: #3fb950; font-size: 20px; font-weight: bold; }
    .stop-red { color: #f85149; font-size: 20px; font-weight: bold; }

    /* TAB 5: DEDEKTİF KARTI */
    .detective-card { background-color: #161b22; border: 2px solid #58a6ff; border-radius: 15px; padding: 30px; text-align: center; }
    .detective-label { font-size: 14px; color: #8b949e; letter-spacing: 1px; }
    .detective-value { font-size: 32px; font-weight: bold; color: white; margin-bottom: 15px; }
    
    .text-green { color: #3fb950 !important; } .text-red { color: #f85149 !important; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
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
        df['Guven_Skoru_Num'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(0)
        # Sadece WATCHLIST'i filtrele
        df = df[df['Hisse'].isin(FULL_WATCHLIST)]
        return df
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
        ozet = []
        if rsi < 30: score += 25; ozet.append(f"RSI Dipte ({rsi:.0f})")
        elif rsi < 40: score += 10; ozet.append(f"RSI Ucuz ({rsi:.0f})")
        elif rsi > 70: score -= 20; ozet.append("RSI Tepede")
        
        if curr_price > sma200: score += 15
        else: score -= 10
        
        karar = "BEKLE"
        if score >= 75: karar = "GÜÇLÜ AL"
        elif score >= 60: karar = "AL"
        elif score <= 30: karar = "SAT"
        return {
            'Hisse': ticker, 'Fiyat': curr_price, 'Karar': karar, 'Guven_Skoru_Num': score,
            'Hedef_Fiyat': curr_price * 1.05, 'Stop_Loss': curr_price * 0.95,
            'Vade': "1-2 Hafta", 'Analiz_Ozeti': " | ".join(ozet)
        }
    except: return None

# --- 4. ANA EKRAN ---
st.title("🌾 Sazlık Pro: Komuta Merkezi")
st.markdown(f"**Aktif Özel Tim:** `{', '.join(FULL_WATCHLIST)}`")
st.markdown("---")

# Veri Ayrıştırma (Eski Sürümden)
robot_picks = pd.DataFrame()
ai_picks = pd.DataFrame()
if not df.empty:
    robot_picks = df[df['Analiz_Ozeti'].str.contains('GARANTİCİ BABA', na=False) | (df['Haber_Baslik'] == "Teknik Tarama (Haber Yok)") if 'Haber_Baslik' in df.columns else df['Analiz_Ozeti'].str.contains('Teknik', na=False)]
    ai_picks = df[~df.index.isin(robot_picks.index)]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 AI Vitrini", "📊 Portföy Analizi", "🧪 250$ Deney Labı", "🗃️ Veri Havuzu", "🔎 Hisse Dedektifi"
])

# --- TAB 1: AI VİTRİNİ (GERİ GELDİ) ---
with tab1:
    if not ai_picks.empty:
        top_picks = ai_picks.sort_values('Guven_Skoru_Num', ascending=False)
        c1, c2, c3 = st.columns(3)
        top3 = top_picks.head(3).reset_index()
        
        def create_vitrin_card(row, rank):
            score = int(row['Guven_Skoru_Num'])
            color = "#238636" if score >= 85 else "#1f6feb" if score >= 70 else "#d29922"
            html = f"""<div class="top-card"><div style="color:#58a6ff; font-weight:bold; font-size:12px;">#{rank} NUMARA</div><div class="top-symbol">{row['Hisse']}</div><div class="top-price">{safe_val(row['Fiyat'], '$')}</div><div class="top-vade">{safe_val(row['Vade'])}</div><div style="display:flex; justify-content:center; gap:5px; align-items:baseline;"><span style="color:#888;">PUAN:</span><span class="top-score" style="color:{color};">{score}</span><span style="color:#888;">/100</span></div><hr style="border-color:#30363d; margin:15px 0;"><div style="display:flex; justify-content:space-between; font-size:14px;"><div style="text-align:left;"><div style="color:#888; font-size:11px;">HEDEF</div><div class="text-green" style="font-weight:bold; font-size:18px;">{safe_val(row['Hedef_Fiyat'], '$')}</div><div class="text-green">{safe_val(row['Kazanc_Potansiyeli'])}</div></div><div style="text-align:right;"><div style="color:#888; font-size:11px;">STOP</div><div class="text-red" style="font-weight:bold; font-size:18px;">{safe_val(row['Stop_Loss'], '$')}</div><div class="text-red">{safe_val(row['Risk_Yuzdesi'])}</div></div></div></div>"""
            return html
        
        if len(top3) > 0: c1.markdown(create_vitrin_card(top3.iloc[0], 1), unsafe_allow_html=True)
        if len(top3) > 1: c2.markdown(create_vitrin_card(top3.iloc[1], 2), unsafe_allow_html=True)
        if len(top3) > 2: c3.markdown(create_vitrin_card(top3.iloc[2], 3), unsafe_allow_html=True)
        
        st.dataframe(top_picks, use_container_width=True)
    else:
        st.info("AI Vitrini için yeterli veri yok.")

# --- TAB 2: PORTFÖY ANALİZİ (GERİ GELDİ) ---
with tab2:
    if not df.empty:
        efsane = df[df['Guven_Skoru_Num'] >= 85]
        iyi = df[(df['Guven_Skoru_Num'] >= 70) & (df['Guven_Skoru_Num'] < 85)]
        orta = df[(df['Guven_Skoru_Num'] >= 50) & (df['Guven_Skoru_Num'] < 70)]
        cop = df[df['Guven_Skoru_Num'] < 50]

        c1, c2, c3, c4 = st.columns(4)
        
        def create_infobox(title, count, desc, bg_class, items_df):
            items_html = ""
            for _, row in items_df.head(5).iterrows():
                items_html += f"<div class='stock-item'><span><b>{row['Hisse']}</b></span><span>{int(row['Guven_Skoru_Num'])} Puan</span></div>"
            return f"""<div class="info-box {bg_class}"><div class="info-title">{title}</div><div class="info-count">{count}</div><div class="info-desc">{desc}</div><hr style="border-color:rgba(255,255,255,0.2); margin:10px 0;"><div style="text-align:left;">{items_html}</div></div>"""

        with c1: st.markdown(create_infobox("💎 Mükemmel", len(efsane), "Kaçırma", "bg-legend", efsane), unsafe_allow_html=True)
        with c2: st.markdown(create_infobox("🚀 İyi", len(iyi), "Güçlü", "bg-good", iyi), unsafe_allow_html=True)
        with c3: st.markdown(create_infobox("⚖️ Orta", len(orta), "Takip Et", "bg-mid", orta), unsafe_allow_html=True)
        with c4: st.markdown(create_infobox("⛔ Uzak Dur", len(cop), "Riskli", "bg-bad", cop), unsafe_allow_html=True)
    else:
        st.warning("Veri bekleniyor.")

# ==============================================================================
# --- TAB 3: SNIPER BARON LABORATUVARI (YENİ GÖRSEL TASARIM) ---
# ==============================================================================
with tab3:
    st.markdown("## 🧪 250$ Deney Laboratuvarı")
    
    col_in, col_inf = st.columns([1, 2])
    budget = col_in.number_input("Kasa ($)", value=250.0, step=10.0)
    trade_budget = budget * 0.98
    col_inf.success(f"**Savaş Bütçesi:** ${trade_budget:.2f} (Kasanın %98'i)")

    if st.button("🚀 Piyasayı Tara ve Emri Ver", type="primary"):
        with st.spinner("Hesaplanıyor..."):
            opportunities = []
            for ticker in FULL_WATCHLIST:
                res = analyze_sniper(ticker)
                if res and res["Durum"] == "AL (SNIPER)":
                    opportunities.append(res)
            
            opportunities.sort(key=lambda x: x["RSI"], reverse=True)
            
            if not opportunities:
                st.warning("### 💤 Pusuya Devam")
                st.write("Atış menzilinde hisse yok.")
            else:
                plan_a = opportunities[0]
                plan_b = opportunities[1] if len(opportunities) > 1 else None
                
                # HTML KART RENDER FONKSİYONU
                def render_card(plan, title, is_plan_b=False):
                    css_class = "op-card-b" if is_plan_b else "op-card"
                    ticker = plan['Hisse']
                    price = plan['Fiyat']
                    rsi = plan['RSI']
                    
                    target = price * 1.10
                    stop = price * 0.92
                    
                    adet = int(trade_budget / price)
                    
                    if adet == 0:
                        warn_class = "op-instruction-warning"
                        msg = f"""
                        <b>⚠️ BÜTÇE YETERSİZ!</b><br>
                        Paran (${trade_budget:.2f}), 1 adet {ticker} almaya yetmiyor (${price:.2f}).<br>
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

                    html = f"""
                    <div class="{css_class}">
                        <div class="op-header">
                            <div class="op-title">{title}: {ticker}</div>
                            <div class="op-badge">RSI: {rsi:.1f}</div>
                        </div>
                        <div class="op-grid">
                            <div><div class="op-label">GİRİŞ FİYATI</div><div class="op-value">${price:.2f}</div></div>
                            <div style="text-align:right;"><div class="op-label">YATIRILACAK</div><div class="op-value">${trade_budget:.2f}</div></div>
                        </div>
                        <div class="{warn_class}">{msg}</div>
                        <div class="op-footer">
                            <div><div class="op-label">HEDEF 1 (KAR AL)</div><div class="target-green">${target:.2f}</div><div style="font-size:11px; color:#8b949e;">%10 Kar</div></div>
                            <div style="text-align:right;"><div class="op-label">STOP LOSS</div><div class="stop-red">${stop:.2f}</div><div style="font-size:11px; color:#8b949e;">%8 Zarar</div></div>
                        </div>
                    </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)

                st.markdown(f"### 🔥 TESPİT EDİLEN FIRSATLAR ({len(opportunities)} Adet)")
                render_card(plan_a, "PLAN A (ANA HEDEF)", is_plan_b=False)
                
                if plan_b:
                    st.markdown("👇 **Eğer Plan A bütçeni aşıyorsa:**")
                    render_card(plan_b, "PLAN B (YEDEK GÜÇ)", is_plan_b=True)
                elif plan_a and int(trade_budget / plan_a['Fiyat']) == 0:
                    st.warning("⚠️ Plan A bütçeni aşıyor ve başka alternatif yok.")

# --- TAB 4: VERİ HAVUZU ---
with tab4:
    st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True)

# --- TAB 5: DEDEKTİF ---
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
