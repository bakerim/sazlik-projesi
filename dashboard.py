import streamlit as st
import pandas as pd
import altair as alt

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
    .top-symbol { font-size: 36px; font-weight: 900; color: #ffffff; }
    .top-score { font-size: 48px; font-weight: bold; line-height: 1; }
    .top-vade { font-size: 14px; color: #8b949e; margin-bottom: 10px; font-style: italic; }
    
    /* DEDEKTİF KARTI (5. SEKME İÇİN ÖZEL) */
    .detective-card {
        background-color: #0d1117;
        border: 2px solid #58a6ff; /* Mavi Çerçeve */
        border-radius: 15px;
        padding: 30px;
        text-align: center;
    }
    .detective-label { font-size: 14px; color: #8b949e; letter-spacing: 1px; }
    .detective-value { font-size: 32px; font-weight: bold; color: white; margin-bottom: 15px; }
    
    /* RENKLER */
    .text-green { color: #3fb950 !important; }
    .text-red { color: #f85149 !important; }
    
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

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

# --- 4. ANA EKRAN ---
st.title("🌾 Sazlık Pro: Komuta Merkezi")
st.markdown("---")

if df.empty:
    st.info("📡 Veri bekleniyor... Bot şu an çalışıyor.")
    if st.button("Yenile"): st.rerun()

else:
    # VERİ AYRIŞTIRMA
    robot_picks = df[df['Analiz_Ozeti'].str.contains('GARANTİCİ BABA', na=False) | (df['Haber_Baslik'] == "Teknik Tarama (Haber Yok)")]
    ai_picks = df[~df.index.isin(robot_picks.index)]

    # 5 SEKMELİ YAPI
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 AI Vitrini", 
        "📅 Portföy Planı", 
        "👴 Garantici Baba", 
        "🗃️ Tüm Veriler",
        "🔎 Hisse Dedektifi"
    ])

    # --- SEKME 1: AI VİTRİNİ ---
    with tab1:
        top_picks = ai_picks.sort_values('Guven_Skoru_Num', ascending=False)
        if not top_picks.empty:
            col1, col2, col3 = st.columns(3)
            top3 = top_picks.head(3).reset_index()
            
            def create_vitrin_card(row, rank):
                score = int(row['Guven_Skoru_Num'])
                color = "#238636" if score >= 85 else "#1f6feb" if score >= 70 else "#d29922"
                html = f"""
                <div class="top-card">
                    <div style="color:#58a6ff; font-weight:bold; font-size:12px;">#{rank} NUMARA</div>
                    <div class="top-symbol">{row['Hisse']}</div>
                    <div class="top-vade">{safe_val(row['Vade'])}</div>
                    <div style="display:flex; justify-content:center; gap:5px; align-items:baseline;">
                        <span style="color:#888;">PUAN:</span>
                        <span class="top-score" style="color:{color};">{score}</span>
                        <span style="color:#888;">/100</span>
                    </div>
                    <hr style="border-color:#30363d; margin:15px 0;">
                    <div style="display:flex; justify-content:space-between; font-size:14px;">
                        <div style="text-align:left;">
                            <div style="color:#888; font-size:11px;">HEDEF</div>
                            <div class="text-green" style="font-weight:bold; font-size:18px;">{safe_val(row['Hedef_Fiyat'], '$')}</div>
                            <div class="text-green">{safe_val(row['Kazanc_Potansiyeli'])}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="color:#888; font-size:11px;">STOP</div>
                            <div class="text-red" style="font-weight:bold; font-size:18px;">{safe_val(row['Stop_Loss'], '$')}</div>
                            <div class="text-red">{safe_val(row['Risk_Yuzdesi'])}</div>
                        </div>
                    </div>
                </div>
                """
                return html

            if len(top3) > 0: col1.markdown(create_vitrin_card(top3.iloc[0], 1), unsafe_allow_html=True)
            if len(top3) > 1: col2.markdown(create_vitrin_card(top3.iloc[1], 2), unsafe_allow_html=True)
            if len(top3) > 2: col3.markdown(create_vitrin_card(top3.iloc[2], 3), unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📋 Liste Görünümü")
            st.dataframe(top_picks[['Guven_Skoru', 'Hisse', 'Vade', 'Hedef_Fiyat', 'Stop_Loss', 'Analiz_Ozeti']], use_container_width=True)
        else:
            st.info("Haber kaynaklı fırsat bulunamadı.")

    # --- SEKME 2: PORTFÖY ---
    with tab2:
        buy_signals = df[df['Karar'].str.contains('AL', na=False)]
        if not buy_signals.empty:
            chart = alt.Chart(buy_signals).mark_arc(innerRadius=60).encode(
                theta=alt.Theta(field="Guven_Skoru_Num", type="quantitative"),
                color=alt.Color(field="Hisse", type="nominal"),
                tooltip=["Hisse", "Vade", "Guven_Skoru"]
            ).properties(height=350)
            st.altair_chart(chart, use_container_width=True)
            st.dataframe(buy_signals[['Hisse', 'Vade', 'Kasa_Yonetimi']], use_container_width=True)
        else:
            st.warning("'AL' sinyali yok.")

    # --- SEKME 3: ROBOT ---
    with tab3:
        if not robot_picks.empty:
            st.dataframe(robot_picks[['Guven_Skoru', 'Hisse', 'Vade', 'Hedef_Fiyat', 'Stop_Loss', 'Analiz_Ozeti']], use_container_width=True)
        else:
            st.info("Robot henüz veri topluyor.")

    # --- SEKME 4: TÜM VERİ ---
    with tab4:
        st.dataframe(df, use_container_width=True)

    # --- SEKME 5: HİSSE DEDEKTİFİ (YENİ) ---
    with tab5:
        st.header("🔎 Hisse Dedektifi")
        
        # Hisse Seçim Kutusu
        all_tickers = sorted(df['Hisse'].unique())
        selected_ticker = st.selectbox("İncelemek İstediğiniz Hisseyi Seçin:", all_tickers)
        
        if selected_ticker:
            # Seçilen hissenin verisini çek
            row = df[df['Hisse'] == selected_ticker].iloc[0]
            
            score = int(row['Guven_Skoru_Num'])
            score_color = "#238636" if score >= 85 else "#1f6feb" if score >= 70 else "#d29922"
            
            # --- DEDEKTİF KARTI ---
            col_det1, col_det2 = st.columns([1, 2])
            
            with col_det1:
                st.markdown(f"""
                <div class="detective-card">
                    <div style="font-size:40px; font-weight:900; color:white;">{row['Hisse']}</div>
                    <div style="font-size:16px; color:#888; margin-bottom:20px;">{safe_val(row['Vade'])}</div>
                    
                    <div style="font-size:60px; font-weight:bold; color:{score_color}; line-height:1;">{score}</div>
                    <div style="font-size:12px; color:#888; letter-spacing:2px;">PUAN</div>
                    
                    <hr style="border-color:#30363d; margin:20px 0;">
                    <div style="font-size:24px; font-weight:bold; color:white;">{row['Karar']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_det2:
                # Metrikler
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"<div class='detective-label'>HEDEF FİYAT</div><div class='detective-value text-green'>{safe_val(row['Hedef_Fiyat'], '$')}</div><div style='color:#3fb950'>{safe_val(row['Kazanc_Potansiyeli'])}</div>", unsafe_allow_html=True)
                c2.markdown(f"<div class='detective-label'>STOP LOSS</div><div class='detective-value text-red'>{safe_val(row['Stop_Loss'], '$')}</div><div style='color:#f85149'>{safe_val(row['Risk_Yuzdesi'])}</div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='detective-label'>GİRİŞ FİYATI</div><div class='detective-value'>{safe_val(row['Fiyat'], '$')}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("📝 Analiz Raporu")
                st.info(row['Analiz_Ozeti'])
                
                if row['Link'] and str(row['Link']) != '-':
                    st.markdown(f"[Haberi Kaynağında Oku 🔗]({row['Link']})")
