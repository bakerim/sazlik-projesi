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
    
    /* İNFOGRAFİK KUTULARI */
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
    
    .bg-legend { background: linear-gradient(135deg, #1a7f37 0%, #2da44e 100%); } 
    .bg-good { background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%); }   
    .bg-mid { background: linear-gradient(135deg, #9e6a03 0%, #d29922 100%); }     
    .bg-bad { background: linear-gradient(135deg, #da3633 0%, #f85149 100%); }     

    /* HİSSE LİSTESİ */
    .stock-item {
        background-color: rgba(0,0,0,0.2);
        padding: 8px;
        margin: 5px 0;
        border-radius: 5px;
        display: flex;
        justify-content: space-between;
        font-size: 14px;
    }

    /* OPERASYON KARTI (TAB 3) */
    .op-card {
        background-color: #0d1117;
        border: 2px solid #3fb950;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .op-card-b { border-color: #8b949e; opacity: 0.8; }
    .op-header {
        font-size: 24px; font-weight: 900; color: white;
        border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 15px;
        display: flex; justify-content: space-between;
    }
    .op-step {
        background: rgba(255,255,255,0.05);
        padding: 10px; border-radius: 5px; margin: 5px 0;
        font-size: 15px; color: #e6edf3; line-height: 1.6;
    }
    .op-label { color: #8b949e; font-size: 12px; font-weight: bold; letter-spacing: 1px; }
    .op-value { font-size: 18px; font-weight: bold; color: white; }
    .op-target { color: #3fb950 !important; }
    .op-stop { color: #f85149 !important; }

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

# --- İZLEME LİSTESİ (ÖZEL TİM) ---
FULL_WATCHLIST = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "PLTR", "MSTR", "COIN"
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
        
        # Sadece WATCHLIST içindeki hisseleri filtrele
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

# --- SNIPER BARON ANALİZ MOTORU (V13.0) ---
def analyze_sniper(ticker):
    """V13 Sniper Baron Stratejisine göre anlık analiz eder"""
    try:
        df_sniper = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df_sniper.columns, pd.MultiIndex):
            df_sniper.columns = df_sniper.columns.get_level_values(0)
        
        if len(df_sniper) < 200: return None
        
        # İndikatörler
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
        
        # STRATEJİ KURALLARI
        trend_score = 1 if (close > sma200 and close > sma50) else 0
        momentum_score = 1 if rsi >= 55 else 0
        trigger = close > sma20
        
        if trend_score and momentum_score and trigger:
            durum = "AL (SNIPER)"
        elif close < sma50: 
            durum = "SAT"
        
        return {
            "Hisse": ticker,
            "Fiyat": close,
            "RSI": rsi,
            "Durum": durum
        }
    except:
        return None

# --- CANLI ANALİZ (Dedektif İçin) ---
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
st.markdown(f"**Aktif Özel Tim:** `{', '.join(FULL_WATCHLIST)}`")
st.markdown("---")

if df.empty:
    st.info("📡 Veri bekleniyor veya listede uygun sinyal yok...")

# VERİ AYRIŞTIRMA
robot_picks = pd.DataFrame()
ai_picks = pd.DataFrame()
if not df.empty:
    df_filtered = df[df['Hisse'].isin(FULL_WATCHLIST)]
    if not df_filtered.empty:
        robot_picks = df_filtered[df_filtered['Analiz_Ozeti'].str.contains('GARANTİCİ BABA', na=False) | (df_filtered['Haber_Baslik'] == "Teknik Tarama (Haber Yok)")]
        ai_picks = df_filtered[~df_filtered.index.isin(robot_picks.index)]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 AI Vitrini", 
    "📊 Portföy Analizi", 
    "🧪 250$ Deney Labı", 
    "🗃️ Veri Havuzu",
    "🔎 Hisse Dedektifi"
])

# --- SEKME 1: AI VİTRİNİ (GERİ GELDİ!) ---
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
        st.info("Bu listedeki hisseler için uygun AI fırsatı bulunamadı.")

# --- SEKME 2: PORTFÖY VE KARAR DESTEK (GERİ GELDİ!) ---
with tab2:
    st.subheader("📊 Portföy Karar Destek Matrisi")
    
    df_chart = df[df['Hisse'].isin(FULL_WATCHLIST)] if not df.empty else pd.DataFrame()

    if not df_chart.empty:
        efsane = df_chart[df_chart['Guven_Skoru_Num'] >= 85]
        iyi = df_chart[(df_chart['Guven_Skoru_Num'] >= 70) & (df_chart['Guven_Skoru_Num'] < 85)]
        orta = df_chart[(df_chart['Guven_Skoru_Num'] >= 50) & (df_chart['Guven_Skoru_Num'] < 70)]
        cop = df_chart[df_chart['Guven_Skoru_Num'] < 50]

        c1, c2, c3, c4 = st.columns(4)

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

        with c1: st.markdown(create_infobox("💎 Mükemmel", len(efsane), "Gözün kapalı alabileceğin fırsatlar", "bg-legend", efsane), unsafe_allow_html=True)
        with c2: st.markdown(create_infobox("🚀 İyi", len(iyi), "Güçlü yükseliş potansiyeli", "bg-good", iyi), unsafe_allow_html=True)
        with c3: st.markdown(create_infobox("⚖️ Orta", len(orta), "İzlemede kal, henüz net değil", "bg-mid", orta), unsafe_allow_html=True)
        with c4: st.markdown(create_infobox("⛔ Sakın Dokunma", len(cop), "Düşüş trendi veya aşırı riskli", "bg-bad", cop), unsafe_allow_html=True)

    else:
        st.warning("Veri bekleniyor...")

# --- SEKME 3: YENİLENEN SNIPER BARON LABORATUVARI ---
with tab3:
    st.markdown("## 🧪 250$ Deney Laboratuvarı: Operasyon Masası")
    st.markdown("Bu panel, sana ne yapacağını adım adım söyleyen bir robottur. **Yorum katma, uygula.**")
    
    col_input, col_info = st.columns([1, 2])
    with col_input:
        budget = st.number_input("Mevcut Kasa ($)", value=250.0, step=10.0, format="%.2f")
    with col_info:
        trade_budget = budget * 0.98
        st.info(f"**Savaş Bütçesi:** ${trade_budget:.2f} (Kasanın %98'i)\n\n*Komisyon için %2 nakit bırakıldı.*")

    if st.button("🚀 Piyasayı Tara ve Emri Ver", type="primary"):
        with st.spinner("Özel Tim taranıyor... Strateji hesaplanıyor..."):
            opportunities = []
            for ticker in FULL_WATCHLIST:
                res = analyze_sniper(ticker)
                if res and res["Durum"] == "AL (SNIPER)":
                    opportunities.append(res)
            
            opportunities.sort(key=lambda x: x["RSI"], reverse=True)
            
            if not opportunities:
                st.warning("### 💤 Pusuya Devam")
                st.write("Şu an hiçbir hisse Sniper kriterlerini karşılamıyor.")
            else:
                plan_a = opportunities[0]
                plan_b = opportunities[1] if len(opportunities) > 1 else None
                
                def render_operation_card(plan, label, css_class=""):
                    ticker = plan['Hisse']
                    price = plan['Fiyat']
                    rsi = plan['RSI']
                    
                    yatirim_tutari = trade_budget
                    hedef_fiyat = price * 1.10
                    stop_fiyat = price * 0.92
                    
                    adet_tam = int(yatirim_tutari / price)
                    kalan_para = yatirim_tutari - (adet_tam * price)

                    # 0 ADET UYARISI
                    if adet_tam == 0:
                        buy_msg = f"<span style='color:#f85149'>⚠️ DİKKAT: Bütçen (${yatirim_tutari:.2f}) bu hissenin 1 tanesine (${price:.2f}) yetmiyor.</span><br>👉 Sadece <b>Parça Hisse (Fractional Share)</b> alabiliyorsan devam et."
                    else:
                        buy_msg = f"- Eğer sadece Tam Hisse alabiliyorsan: <b>{adet_tam} Adet</b> al. (Kalan ${kalan_para:.2f} nakitte dursun)."

                    # DÜZELTİLMİŞ HTML FORMATI (TRIPLE QUOTE KULLANILDI)
                    html_code = f"""
                    <div class="op-card {css_class}">
                        <div class="op-header">
                            <span>{label}: {ticker}</span>
                            <span style="font-size:16px; color:#3fb950;">RSI: {rsi:.1f}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                            <div>
                                <div class="op-label">GİRİŞ FİYATI (Tahmini)</div>
                                <div class="op-value">${price:.2f}</div>
                            </div>
                            <div style="text-align:right;">
                                <div class="op-label">YATIRILACAK TUTAR</div>
                                <div class="op-value">${yatirim_tutari:.2f}</div>
                            </div>
                        </div>
                        
                        <div class="op-step">
                            <b>ADIM 1: SATIN ALMA</b><br>
                            - Eğer Parça Hisse alabiliyorsan: <b>${yatirim_tutari:.2f}</b> tutarında {ticker} al.<br>
                            {buy_msg}
                        </div>
                        
                        <div style="display:flex; justify-content:space-between; margin-top:15px; border-top:1px solid #30363d; padding-top:10px;">
                            <div>
                                <div class="op-label">ALARM 1 (KAR AL)</div>
                                <div class="op-value op-target">${hedef_fiyat:.2f}</div>
                                <div style="font-size:11px; color:#8b949e;">Bu fiyata gelince yarısını sat!</div>
                            </div>
                            <div style="text-align:right;">
                                <div class="op-label">ALARM 2 (STOP)</div>
                                <div class="op-value op-stop">${stop_fiyat:.2f}</div>
                                <div style="font-size:11px; color:#8b949e;">Bu fiyata düşerse kaç!</div>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(html_code, unsafe_allow_html=True)

                st.markdown(f"### 🔥 TESPİT EDİLEN FIRSATLAR ({len(opportunities)} Adet)")
                render_operation_card(plan_a, "PLAN A (Ana Hedef)")
                
                if plan_b:
                    st.markdown("👇 *Eğer Plan A hissesi bütçeni aşıyorsa veya alım yapamıyorsan:*")
                    render_operation_card(plan_b, "PLAN B (Yedek Güç)", "op-card-b")
                elif plan_a and int(trade_budget / plan_a['Fiyat']) == 0:
                     st.warning("⚠️ Plan A için paran yetmiyor ve başka alternatif (Plan B) bulunamadı. Parça hisse alamıyorsan işlem yapma.")

                with st.expander("🧠 Robotun Savaş Taktikleri (Oku!)"):
                    st.markdown("""
                    **1. Panik Yok:** Hisseyi aldıktan sonra fiyat %2-3 düşebilir. Robot "SAT" demediği sürece (veya Stop fiyatına gelmediği sürece) satma.
                    **2. Yarısını Sat:** Fiyat "Kar Al" hedefine ($) geldiği an, elindekilerin tam yarısını sat.
                    **3. Kapanış:** Robotun "SAT" sinyalini bekle.
                    """)

# --- SEKME 4: TÜM VERİ ---
with tab4:
    df_show = df[df['Hisse'].isin(FULL_WATCHLIST)] if not df.empty else pd.DataFrame()
    st.dataframe(df_show, use_container_width=True)

# --- SEKME 5: HİSSE DEDEKTİFİ ---
with tab5:
    st.header("🔎 Hisse Dedektifi")
    selected_ticker = st.selectbox("İncelemek İstediğiniz Hisseyi Seçin:", sorted(FULL_WATCHLIST))
    
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
