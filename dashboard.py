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
    
    /* KART TASARIMI */
    .top-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }
    .top-rank {
        font-size: 12px;
        color: #58a6ff;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .top-symbol {
        font-size: 36px;
        font-weight: 900;
        color: #ffffff;
        line-height: 1.2;
    }
    .top-vade {
        font-size: 14px;
        color: #8b949e;
        margin-bottom: 15px;
        font-style: italic;
    }
    .score-container {
        display: flex;
        justify-content: center;
        align-items: baseline;
        gap: 5px;
        margin-bottom: 15px;
    }
    .top-score {
        font-size: 48px;
        font-weight: bold;
        line-height: 1;
    }
    
    /* RENK SINIFLARI */
    .text-green { color: #3fb950 !important; }
    .text-red { color: #f85149 !important; }
    .text-gray { color: #8b949e !important; }
    
    /* ROBOT KARTI (GARANTİCİ BABA İÇİN) */
    .robot-card {
        border-left: 4px solid #a371f7; /* Mor Çizgi */
        background-color: #161b22;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 4px;
    }
    
    /* TABLO DÜZENİ */
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 3. VERİ YÜKLEME VE TEMİZLEME ---
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv("sazlik_signals.csv", on_bad_lines='skip', engine='python')
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        
        # Gerekli sütunlar yoksa oluştur
        required = ['Hisse', 'Fiyat', 'Karar', 'Guven_Skoru', 'Hedef_Fiyat', 'Stop_Loss', 
                    'Vade', 'Kasa_Yonetimi', 'Risk_Yuzdesi', 'Kazanc_Potansiyeli', 'Analiz_Ozeti']
        for col in required:
            if col not in df.columns: df[col] = "-"
            
        # Her hissenin sadece EN GÜNCEL halini al
        df = df.sort_values('Tarih', ascending=False).drop_duplicates('Hisse')
        
        # Sayısal dönüşümler
        df['Guven_Skoru_Num'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(0)
        
        return df
    except:
        return pd.DataFrame()

# Veriyi başlat
df = pd.DataFrame()
df = load_data()

# --- YARDIMCI FONKSİYON: NAN TEMİZLEYİCİ ---
def safe_val(val, prefix=""):
    """Değer 'nan', 0 veya boşsa '-' döner, değilse değeri döner."""
    try:
        if pd.isna(val) or str(val).lower() == 'nan' or str(val).strip() == "" or val == 0:
            return '<span class="text-gray">-</span>'
        return f"{prefix}{val}"
    except:
        return '<span class="text-gray">-</span>'

# --- 4. ANA EKRAN ---
st.title("🌾 Sazlık Pro: Komuta Merkezi")
st.markdown("---")

if df.empty:
    st.info("📡 Veri bekleniyor... Bot şu an haberleri tarıyor.")
    if st.button("Yenile"): st.rerun()

else:
    # --- VERİLERİ AYIRIŞTIR (AI vs ROBOT) ---
    # Garantici Baba verileri "Haber Yok" başlığına veya "GARANTİCİ BABA" etiketine sahiptir
    robot_picks = df[df['Analiz_Ozeti'].str.contains('GARANTİCİ BABA', na=False) | (df['Haber_Baslik'] == "Teknik Tarama (Haber Yok)")]
    ai_picks = df[~df.index.isin(robot_picks.index)] # Robot olmayanlar AI'dır

    # --- SEKMELER ---
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 AI Vitrini (Haber)", "📅 Portföy Planı", "👴 Garantici Baba (Teknik)", "🗃️ Tüm Veriler"])

    # =========================================================================
    # SEKME 1: AI VİTRİNİ
    # =========================================================================
    with tab1:
        st.caption("📰 Sadece hakkında HABER olan ve Yapay Zeka tarafından seçilen hisseler.")
        
        # Puanına göre sırala
        top_picks = ai_picks.sort_values('Guven_Skoru_Num', ascending=False)
        
        if not top_picks.empty:
            col1, col2, col3 = st.columns(3)
            top3 = top_picks.head(3).reset_index()
            
            # KART OLUŞTURUCU
            def create_card(row, rank):
                hedef = safe_val(row.get('Hedef_Fiyat'), "$")
                kazanc = safe_val(row.get('Kazanc_Potansiyeli'))
                stop = safe_val(row.get('Stop_Loss'), "$")
                risk = safe_val(row.get('Risk_Yuzdesi'))
                vade = safe_val(row.get('Vade'))
                score = int(row['Guven_Skoru_Num'])
                score_color = "#238636" if score >= 85 else "#1f6feb" if score >= 70 else "#d29922"
                
                html = f"""
                <div class="top-card">
                <div class="top-rank">#{rank} NUMARA</div>
                <div class="top-symbol">{row['Hisse']}</div>
                <div class="top-vade">{vade}</div>
                <div class="score-container">
                <span style="font-size:14px; color:#888;">PUAN:</span>
                <span class="top-score" style="color:{score_color};">{score}</span>
                <span style="font-size:16px; color:#888;">/100</span>
                </div>
                <hr style="border-color:#30363d; margin:15px 0;">
                <div style="display:flex; justify-content:space-between; font-size:14px;">
                <div style="text-align:left;">
                <div style="color:#888; font-size:11px;">HEDEF</div>
                <div class="text-green" style="font-weight:bold; font-size:18px;">{hedef}</div>
                <div class="text-green" style="font-size:12px;">{kazanc}</div>
                </div>
                <div style="text-align:right;">
                <div style="color:#888; font-size:11px;">STOP</div>
                <div class="text-red" style="font-weight:bold; font-size:18px;">{stop}</div>
                <div class="text-red" style="font-size:12px;">{risk}</div>
                </div>
                </div>
                </div>
                """
                return html

            # Kartları yerleştir
            if len(top3) > 0: col1.markdown(create_card(top3.iloc[0], 1), unsafe_allow_html=True)
            if len(top3) > 1: col2.markdown(create_card(top3.iloc[1], 2), unsafe_allow_html=True)
            if len(top3) > 2: col3.markdown(create_card(top3.iloc[2], 3), unsafe_allow_html=True)

            st.markdown("---")

            # --- ALT TABLO ---
            st.subheader("📋 AI Detaylı Liste")
            table_df = top_picks.iloc[3:].copy()
            if table_df.empty: table_df = top_picks.copy()

            display_df = table_df[[
                'Guven_Skoru_Num', 'Hisse', 'Karar', 'Fiyat', 'Hedef_Fiyat', 
                'Stop_Loss', 'Kasa_Yonetimi', 'Vade', 'Analiz_Ozeti'
            ]].copy()
            
            display_df = display_df.fillna("-")
            display_df.columns = ['AI Puanı', 'Sembol', 'Trend', 'Giriş ($)', 'Hedef ($)', 'Stop ($)', 'Kasa %', 'Vade', 'AI Açıklaması']

            st.dataframe(
                display_df,
                column_config={
                    "AI Puanı": st.column_config.ProgressColumn("AI Puanı", format="%d", min_value=0, max_value=100),
                    "AI Açıklaması": st.column_config.TextColumn("AI Açıklaması", width="large")
                },
                hide_index=True,
                use_container_width=True,
                height=500
            )
        else:
            st.info("Şu an gündemde yapay zekanın dikkatini çeken bir haber yok.")

    # =========================================================================
    # SEKME 2: PORTFÖY PLANLAYICI
    # =========================================================================
    with tab2:
        st.subheader("📊 Portföy Dağılım Önerisi")
        buy_signals = df[df['Karar'].str.contains('AL', na=False)]
        
        if not buy_signals.empty:
            col_p1, col_p2 = st.columns([1, 2])
            with col_p1:
                st.info("💡 **Strateji:**\nGrafik, hem AI (Haber) hem Robot (Teknik) kaynaklı 'AL' sinyallerini içerir.")
            with col_p2:
                chart = alt.Chart(buy_signals).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta(field="Guven_Skoru_Num", type="quantitative"),
                    color=alt.Color(field="Hisse", type="nominal"),
                    tooltip=["Hisse", "Guven_Skoru_Num", "Kasa_Yonetimi"]
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("Şu an 'AL' sinyali yok.")

    # =========================================================================
    # SEKME 3: GARANTİCİ BABA (ROBOT)
    # =========================================================================
    with tab3:
        st.caption("⚙️ Sadece TEKNİK ANALİZ ile bulunan, haberi olmayan sessiz fırsatlar.")
        
        if not robot_picks.empty:
            robot_picks = robot_picks.sort_values('Guven_Skoru_Num', ascending=False)
            
            # Robot verileri için sade ve teknik bir tablo
            st.subheader(f"🔍 Robot {len(robot_picks)} Fırsat Buldu")
            
            # Robot tablosu için sütun seçimi (Haber Başlığına gerek yok)
            robot_display = robot_picks[[
                'Guven_Skoru_Num', 'Hisse', 'Karar', 'Fiyat', 'RSI', 
                'Hedef_Fiyat', 'Stop_Loss', 'Analiz_Ozeti'
            ]].copy()
            
            # RSI Sütunu yoksa oluştur (Eski verilerde olmayabilir)
            if 'RSI' not in robot_display.columns: robot_display['RSI'] = "-"
            
            robot_display.columns = ['Skor', 'Sembol', 'Sinyal', 'Fiyat', 'RSI', 'Hedef', 'Stop', 'Robot Analizi']
            
            # Analiz özetindeki [GARANTİCİ BABA] etiketini temizleyelim daha şık dursun
            robot_display['Robot Analizi'] = robot_display['Robot Analizi'].str.replace(r'\[GARANTİCİ BABA\]: ', '', regex=True)

            st.dataframe(
                robot_display,
                column_config={
                    "Skor": st.column_config.ProgressColumn("Skor", format="%d", min_value=0, max_value=100),
                    "Robot Analizi": st.column_config.TextColumn("Teknik Gerekçe", width="large"),
                    "Sinyal": st.column_config.TextColumn("Sinyal", width="small")
                },
                hide_index=True,
                use_container_width=True,
                height=600
            )
        else:
            st.info("Garantici Baba henüz tarama yapmadı veya kriterlere uyan (RSI < 30 vb.) hisse bulamadı.")
            st.markdown("*Bot çalıştıkça bu liste dolacaktır.*")

    # =========================================================================
    # SEKME 4: HAM VERİLER
    # =========================================================================
    with tab4:
        st.dataframe(df, use_container_width=True)
