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

# --- 2. CSS TASARIMI ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    
    /* VİTRİN KARTI */
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
    
    /* İNFOGRAFİK KUTULARI (PORTFÖY İÇİN) */
    .info-box {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 10px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .info-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
    .info-count { font-size: 42px; font-weight: 900; }
    .info-desc { font-size: 12px; opacity: 0.8; }
    
    .bg-legend { background: linear-gradient(135deg, #1a7f37 0%, #2da44e 100%); } /* Yeşil */
    .bg-good { background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%); }   /* Mavi */
    .bg-mid { background: linear-gradient(135deg, #9e6a03 0%, #d29922 100%); }     /* Sarı */
    .bg-bad { background: linear-gradient(135deg, #da3633 0%, #f85149 100%); }     /* Kırmızı */

    /* HİSSE LİSTESİ (KUTU İÇİ) */
    .stock-item {
        background-color: rgba(0,0,0,0.2);
        padding: 8px;
        margin: 5px 0;
        border-radius: 5px;
        display: flex;
        justify-content: space-between;
        font-size: 14px;
    }

    /* DEDEKTİF KARTI */
    .detective-card {
        background-color: #0d1117;
        border: 2px solid #58a6ff;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
    }
    .detective-label { font-size: 14px; color: #8b949e; letter-spacing: 1px; }
    .detective-value { font-size: 32px; font-weight: bold; color: white; margin-bottom: 15px; }
    
    .text-green { color: #3fb950 !important; }
    .text-red { color: #f85149 !important; }
    
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- İZLEME LİSTESİ ---
FULL_WATCHLIST = [
    # TEKNOLOJİ DEVLERİ
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE", 
    "CRM", "CMCSA", "QCOM", "TXN", "AMGN", "INTC", "CSCO", "VZ", "T", "TMUS",
    "NFLX", "ORCL", "MU", "IBM", "PYPL", "INTU", "AMD", "FTNT", "ADI", "NOW",
    "LRCX", "MRVL", "CDNS", "SNPS", "DXCM", "KLAC", "ROST", "ANSS", "MSCI", "CHTR",
    
    # FİNANS
    "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPY", "BLK", "SCHW",
    "C", "AXP", "CB", "MMC", "AON", "CME", "ICE", "PGR", "ALL", "MET",
    "AIG", "PNC", "USB", "BK", "COF", "TRV", "MCO", "CBOE", "RJF",
    "GPN", "FIS", "ZION", "FITB", "STT", "NDAQ", "RF", "KEY", "CFG", "HBAN",
    
    # SAĞLIK
    "JNJ", "LLY", "UNH", "ABBV", "MRK", "PFE", "DHR", "TMO", "MDT", "SYK",
    "GILD", "BIIB", "VRTX", "BMY", "ISRG", "ABT", "ZTS", "BDX", "BSX",
    "CI", "CVS", "HUM", "HCA", "ELV", "LH", "COO", "ALGN", "HOLX", "DVA",
    "WAT", "RGEN", "IQV", "REGN", "EW", "TECH", "RVTY", "DGX", "INCY", "CRL",
    
    # TÜKETİM
    "PG", "KO", "PEP", "WMT", "COST", "HD", "MCD", "NKE", "LOW", "TGT",
    "SBUX", "MDLZ", "CL", "PM", "MO", "KR", "DG", "EL", "KHC",
    "GIS", "K", "SYY", "APO", "DECK", "BBY", "WHR", "NWSA", "FOXA", "HAS",
    "MAT", "HOG", "GT", "TPR", "TTC", "VFC", "HBI", "KSS", "ULTA",
    
    # SANAYİ & ENERJİ
    "XOM", "CVX", "BRK.B", "LMT", "RTX", "BA", "HON", "MMM", "GE", "GD",
    "CAT", "DE", "EOG", "OXY", "SLB", "COP", "PSX", "MPC", "WMB", "KMI",
    "ETN", "AOS", "EMR", "PCAR", "ROK", "SWK", "TDY", "RSG", "WM", "CARR",
    "ITW", "GWW", "WAB", "AAL", "DAL", "UAL", "LUV", "ALK",
    
    # DİĞER
    "DUK", "NEE", "SO", "EXC", "AEP", "SRE", "WEC", "D", "ED", "XEL",
    "VNQ", "SPG", "PLD", "EQIX", "AMT", "CCI", "HST", "O", "ARE", "PSA",
    "WY", "BXP", "REG", "VTR", "AVB", "ESR", "EPR", "KIM", "FRT",
    "LUMN", "PARA", "FOX", "WBD", "ETSY", "EBAY", "EA", "TTWO", "ZG",
    
    # YENİ NESİL & BÜYÜME
    "ASML", "AMAT", "TSM", "MCHP", "TER", "U", "VEEV", "OKTA", "NET", "CRWD", 
    "DDOG", "ZS", "TEAM", "ADSK", "MSI", "FTV", "WDC", "ZBRA", "SWKS", "QDEL",
    "FSLY", "PLUG", "ENPH", "SEDG", "RUN", "SPWR", "BLDP", "FCEL", "BE", "SOL",
    "LI", "NIO", "XPEV", "RIVN", "LCID", "NKLA", "QS", "GOEV",
    "SQ", "COIN", "HOOD", "UPST", "AFRM", "SOFI", "MQ", "BILL", "TOST", "PAYA",
    "MRNA", "BMRN", "CTAS", "EXEL", "IONS", "XBI", "EDIT", "BEAM", "NTLA", "CRSP",
    "MELI", "ROKU", "PTON", "SPOT", "CHWY", "ZM", "DOCU", "FVRR",
    "PINS", "SNAP", "WIX", "SHOP", "SE", "BABA", "JD", "BIDU", "PDD",
    "ROP", "TT", "FLR", "HUBB", "APH", "ECL", "SHW", "PPG", "FMC",
    "MOS", "CF", "NUE", "STLD", "SAVE", "CAR", "RCL", "CCL", "NCLH", "MGM", "WYNN", "LVS", "PENN", "DKNG", "BYND",
    "RBLX", "UBER", "LYFT", "ABNB", "DOX", "FLT", "PRU", "VLO", "DVN", "APA", "MRO", "HAL",
    "BKR", "FTI", "NOV", "TDW", "PAGP", "ENLC", "PAA", "WES"
]

# --- 3. VERİ YÜKLEME ---
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
        
        # Vade Filtresi
        def vade_filtresi(row):
            vade = str(row['Vade']).lower()
            kazanc_str = str(row['Kazanc_Potansiyeli']).replace('%', '').strip()
            try:
                kazanc = float(kazanc_str)
            except:
                kazanc = 0
            if ("ay" in vade or "month" in vade) and kazanc < 15:
                return False
            return True
            
        df = df[df.apply(vade_filtresi, axis=1)]
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

# --- CANLI ANALİZ ---
def canli_analiz_yap(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if len(hist) < 200: return None
        
        curr_price = hist['Close'].iloc[-1]
        hist.ta.rsi(length=14, append=True)
        hist.ta.sma(length=50, append=True)
        hist.ta.sma(length=200, append=True)
        
        rsi = hist['RSI_14'].iloc[-1]
        sma200 = hist['SMA_200'].iloc[-1]
        
        score = 50
        ozet = []
        vade = "Belirsiz"
        
        if rsi < 30: 
            score += 25; ozet.append(f"RSI Dipte ({rsi:.0f})")
            vade = "3-5 Gün (Tepki)"
        elif rsi < 40: 
            score += 10; ozet.append(f"RSI Ucuz ({rsi:.0f})")
            vade = "1-2 Hafta"
        elif rsi > 70: 
            score -= 20; ozet.append("RSI Tepede")
            vade = "Düzeltme Bekle"
        
        if curr_price > sma200: 
            score += 15; ozet.append("Trend Pozitif")
            if vade == "Belirsiz": vade = "Orta Vade"
        else: 
            score -= 10; ozet.append("Trend Negatif")
        
        karar = "BEKLE"
        if score >= 75: karar = "GÜÇLÜ AL"
        elif score >= 60: karar = "AL"
        elif score <= 30: karar = "SAT"
        
        return {
            'Hisse': ticker,
            'Fiyat': curr_price,
            'Karar': karar,
            'Guven_Skoru_Num': score,
            'Hedef_Fiyat': curr_price * 1.05,
            'Stop_Loss': curr_price * 0.95,
            'Kazanc_Potansiyeli': '%5',
            'Risk_Yuzdesi': '%-5',
            'Vade': vade,
            'Analiz_Ozeti': " | ".join(ozet),
            'Link': f"https://finance.yahoo.com/quote/{ticker}"
        }
    except:
        return None

# --- 4. ANA EKRAN ---
st.title("🌾 Sazlık Pro: Komuta Merkezi")
st.markdown("---")

if df.empty:
    st.info("📡 Veri bekleniyor...")

# VERİ AYRIŞTIRMA
robot_picks = pd.DataFrame()
ai_picks = pd.DataFrame()
if not df.empty:
    robot_picks = df[df['Analiz_Ozeti'].str.contains('GARANTİCİ BABA', na=False) | (df['Haber_Baslik'] == "Teknik Tarama (Haber Yok)")]
    ai_picks = df[~df.index.isin(robot_picks.index)]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 AI Vitrini", 
    "📊 Portföy Analizi", 
    "👴 Garantici Baba", 
    "🗃️ Tüm Veriler",
    "🔎 Hisse Dedektifi"
])

# --- SEKME 1: AI VİTRİNİ ---
with tab1:
    if not ai_picks.empty:
        top_picks = ai_picks.sort_values('Guven_Skoru_Num', ascending=False)
        col1, col2, col3 = st.columns(3)
        top3 = top_picks.head(3).reset_index()
        
        def create_vitrin_card(row, rank):
            score = int(row['Guven_Skoru_Num'])
            color = "#238636" if score >= 85 else "#1f6feb" if score >= 70 else "#d29922"
            
            html = f"""<div class="top-card"><div style="color:#58a6ff; font-weight:bold; font-size:12px;">#{rank} NUMARA</div><div class="top-symbol">{row['Hisse']}</div><div class="top-price">{safe_val(row['Fiyat'], '$')}</div><div class="top-vade">{safe_val(row['Vade'])}</div><div style="display:flex; justify-content:center; gap:5px; align-items:baseline;"><span style="color:#888;">PUAN:</span><span class="top-score" style="color:{color};">{score}</span><span style="color:#888;">/100</span></div><hr style="border-color:#30363d; margin:15px 0;"><div style="display:flex; justify-content:space-between; font-size:14px;"><div style="text-align:left;"><div style="color:#888; font-size:11px;">HEDEF</div><div class="text-green" style="font-weight:bold; font-size:18px;">{safe_val(row['Hedef_Fiyat'], '$')}</div><div class="text-green">{safe_val(row['Kazanc_Potansiyeli'])}</div></div><div style="text-align:right;"><div style="color:#888; font-size:11px;">STOP</div><div class="text-red" style="font-weight:bold; font-size:18px;">{safe_val(row['Stop_Loss'], '$')}</div><div class="text-red">{safe_val(row['Risk_Yuzdesi'])}</div></div></div></div>"""
            return html

        if len(top3) > 0: col1.markdown(create_vitrin_card(top3.iloc[0], 1), unsafe_allow_html=True)
        if len(top3) > 1: col2.markdown(create_vitrin_card(top3.iloc[1], 2), unsafe_allow_html=True)
        if len(top3) > 2: col3.markdown(create_vitrin_card(top3.iloc[2], 3), unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📋 Liste Görünümü")
        st.dataframe(top_picks[['Guven_Skoru', 'Hisse', 'Vade', 'Fiyat', 'Hedef_Fiyat', 'Analiz_Ozeti']], use_container_width=True)
    else:
        st.info("Kriterlere uyan AI fırsatı yok.")

# --- SEKME 2: PORTFÖY VE KARAR DESTEK ---
with tab2:
    st.subheader("📊 Portföy Karar Destek Matrisi")
    
    if not df.empty:
        # Kategorilendirme
        efsane = df[df['Guven_Skoru_Num'] >= 85]
        iyi = df[(df['Guven_Skoru_Num'] >= 70) & (df['Guven_Skoru_Num'] < 85)]
        orta = df[(df['Guven_Skoru_Num'] >= 50) & (df['Guven_Skoru_Num'] < 70)]
        cop = df[df['Guven_Skoru_Num'] < 50]

        # 4 Kolonlu İnfografik Yapı
        c1, c2, c3, c4 = st.columns(4)

        # HTML Helper
        def create_infobox(title, count, desc, bg_class, items_df):
            items_html = ""
            for _, row in items_df.head(5).iterrows():
                items_html += f"<div class='stock-item'><span><b>{row['Hisse']}</b></span><span>{int(row['Guven_Skoru_Num'])} Puan</span></div>"
            
            return f"""
            <div class="info-box {bg_class}">
                <div class="info-title">{title}</div>
                <div class="info-count">{count}</div>
                <div class="info-desc">{desc}</div>
                <hr style="border-color:rgba(255,255,255,0.2); margin:10px 0;">
                <div style="text-align:left;">{items_html}</div>
            </div>
            """

        with c1:
            st.markdown(create_infobox("💎 Mükemmel", len(efsane), "Gözün kapalı alabileceğin fırsatlar", "bg-legend", efsane), unsafe_allow_html=True)
        with c2:
            st.markdown(create_infobox("🚀 İyi", len(iyi), "Güçlü yükseliş potansiyeli", "bg-good", iyi), unsafe_allow_html=True)
        with c3:
            st.markdown(create_infobox("⚖️ Orta", len(orta), "İzlemede kal, henüz net değil", "bg-mid", orta), unsafe_allow_html=True)
        with c4:
            st.markdown(create_infobox("⛔ Sakın Dokunma", len(cop), "Düşüş trendi veya aşırı riskli", "bg-bad", cop), unsafe_allow_html=True)

        st.markdown("---")
        
        # Detaylı Filtreleme (Opsiyonel Grafik)
        st.subheader("📈 Puan Dağılım Grafiği")
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("Guven_Skoru_Num", bin=True, title="Güven Skoru"),
            y=alt.Y('count()', title="Hisse Sayısı"),
            color=alt.Color('Guven_Skoru_Num', scale=alt.Scale(scheme='viridis'), legend=None)
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

    else:
        st.warning("Analiz verisi bekleniyor...")

# --- SEKME 3: ROBOT ---
with tab3:
    if not robot_picks.empty:
        st.dataframe(robot_picks[['Guven_Skoru', 'Hisse', 'Vade', 'Fiyat', 'Hedef_Fiyat', 'Analiz_Ozeti']], use_container_width=True)
    else:
        st.info("Robot verisi yok.")

# --- SEKME 4: TÜM VERİ ---
with tab4:
    st.dataframe(df, use_container_width=True)

# --- SEKME 5: HİSSE DEDEKTİFİ ---
with tab5:
    st.header("🔎 Hisse Dedektifi")
    
    csv_tickers = list(df['Hisse'].unique()) if not df.empty else []
    combined_list = sorted(list(set(FULL_WATCHLIST + csv_tickers)))
    
    selected_ticker = st.selectbox("İncelemek İstediğiniz Hisseyi Seçin:", combined_list)
    
    if st.button("Hisse Analizini Getir"):
        row = None
        if not df.empty and selected_ticker in df['Hisse'].values:
            row = df[df['Hisse'] == selected_ticker].iloc[0]
            st.success("✅ Veri veritabanından getirildi.")
        else:
            with st.spinner(f"{selected_ticker} için canlı piyasa analizi yapılıyor..."):
                row = canli_analiz_yap(selected_ticker)
                if row: st.success("⚡ Canlı analiz tamamlandı.")
                else: st.error("Veri çekilemedi.")
        
        if row is not None:
            score = int(row['Guven_Skoru_Num']) if 'Guven_Skoru_Num' in row else 50
            score_color = "#238636" if score >= 85 else "#1f6feb" if score >= 70 else "#d29922"
            
            ozet_temiz = str(row['Analiz_Ozeti']).replace("<div>", "").replace("</div>", "").replace("<br>", " ")

            col_det1, col_det2 = st.columns([1, 2])
            with col_det1:
                st.markdown(f"""<div class="detective-card"><div style="font-size:40px; font-weight:900; color:white;">{row['Hisse']}</div><div style="font-size:16px; color:#888; margin-bottom:20px;">{safe_val(row['Vade'])}</div><div style="font-size:60px; font-weight:bold; color:{score_color}; line-height:1;">{score}</div><div style="font-size:12px; color:#888; letter-spacing:2px;">PUAN</div><hr style="border-color:#30363d; margin:20px 0;"><div style="font-size:24px; font-weight:bold; color:white;">{row['Karar']}</div></div>""", unsafe_allow_html=True)
            
            with col_det2:
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"<div class='detective-label'>HEDEF FİYAT</div><div class='detective-value text-green'>{safe_val(row['Hedef_Fiyat'], '$')}</div>", unsafe_allow_html=True)
                c2.markdown(f"<div class='detective-label'>STOP LOSS</div><div class='detective-value text-red'>{safe_val(row['Stop_Loss'], '$')}</div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='detective-label'>GÜNCEL FİYAT</div><div class='detective-value'>{safe_val(row['Fiyat'], '$')}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("📝 Analiz Raporu")
                st.info(ozet_temiz)
                if 'Link' in row and str(row['Link']) != '-':
                    st.markdown(f"[Haberi Kaynağında Oku 🔗]({row['Link']})")
