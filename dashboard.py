import streamlit as st
import pandas as pd
import altair as alt

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Projesi: Günlük Bülten",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS TASARIMI (DARK MODE UYUMLU) ---
st.markdown("""
<style>
    /* Genel Ayarlar */
    .stApp { background-color: #0e1117; }
    
    /* VİTRİN KARTLARI (TOP 3) */
    .top-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        height: 100%;
    }
    .top-rank {
        font-size: 14px;
        color: #58a6ff;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .top-symbol {
        font-size: 32px;
        font-weight: 900;
        color: white;
    }
    .top-score {
        font-size: 42px;
        font-weight: bold;
        color: #238636; /* Yeşil */
    }
    
    /* RENKLER */
    .text-green { color: #3fb950; }
    .text-red { color: #f85149; }
    .text-gray { color: #8b949e; }
    
    /* TABLO BAŞLIKLARI */
    .stDataFrame { border: 1px solid #30363d; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 3. VERİ YÜKLEME ---
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv("sazlik_signals.csv", on_bad_lines='skip', engine='python')
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        
        # Gerekli sütunları oluştur (Yoksa)
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

# Değişkeni başlat
df = pd.DataFrame()
df = load_data()

# --- 4. ANA BAŞLIK ---
st.title("🌾 Sazlık Projesi: Günlük Bülten")
st.markdown(f"**Analiz Edilen Hisse:** {len(df)} | **Son Güncelleme:** {df['Tarih'].max() if not df.empty else '-'}")
st.markdown("---")

if df.empty:
    st.info("📡 Veri bekleniyor... Bot şu an haberleri tarıyor.")
    if st.button("Yenile"): st.rerun()

else:
    # --- SEKMELERİ OLUŞTUR ---
    tab1, tab2, tab3 = st.tabs(["🏆 AI Seçkisi (Top 10)", "📅 Portföy Planlayıcı", "🗃️ Tüm Veriler"])

    # =========================================================================
    # SEKME 1: AI SEÇKİSİ (VİTRİN + LİSTE)
    # =========================================================================
    with tab1:
        # Puanına göre sırala
        top_picks = df.sort_values('Guven_Skoru_Num', ascending=False)
        
        # --- ÜST BÖLÜM: TOP 3 KARTLAR ---
        st.subheader("🌟 Yapay Zeka'nın Favorileri (Top 3)")
        
        col1, col2, col3 = st.columns(3)
        top3 = top_picks.head(3).reset_index()
        
        # Kartları oluşturacak fonksiyon
        def create_card(row, rank):
            return f"""
            <div class="top-card">
                <div class="top-rank">#{rank} NUMARA</div>
                <div class="top-symbol">{row['Hisse']}</div>
                <div style="font-size:14px; color:#8b949e; margin-bottom:10px;">{row.get('Vade', '-')}</div>
                
                <div style="display:flex; justify-content:center; align-items:baseline; gap:5px;">
                    <span style="font-size:14px; color:#888;">PUAN:</span>
                    <span class="top-score">{int(row['Guven_Skoru_Num'])}</span>
                    <span style="font-size:16px; color:#888;">/100</span>
                </div>
                
                <hr style="border-color:#30363d; margin:15px 0;">
                
                <div style="display:flex; justify-content:space-between; font-size:14px;">
                    <div style="text-align:left;">
                        <div style="color:#888;">HEDEF</div>
                        <div class="text-green" style="font-weight:bold;">${row.get('Hedef_Fiyat', '-')}</div>
                        <div class="text-green" style="font-size:11px;">{row.get('Kazanc_Potansiyeli', '-')}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#888;">STOP</div>
                        <div class="text-red" style="font-weight:bold;">${row.get('Stop_Loss', '-')}</div>
                        <div class="text-red" style="font-size:11px;">{row.get('Risk_Yuzdesi', '-')}</div>
                    </div>
                </div>
            </div>
            """

        # Kartları yerleştir (Eğer veri varsa)
        if len(top3) > 0: col1.markdown(create_card(top3.iloc[0], 1), unsafe_allow_html=True)
        if len(top3) > 1: col2.markdown(create_card(top3.iloc[1], 2), unsafe_allow_html=True)
        if len(top3) > 2: col3.markdown(create_card(top3.iloc[2], 3), unsafe_allow_html=True)

        st.markdown("---")

        # --- ALT BÖLÜM: DETAYLI TABLO (4. ve Sonrası) ---
        st.subheader("📋 Listenin Devamı (Detaylı Analiz)")
        
        # Tablo için özel bir görünüm hazırlayalım (Kullanıcı dostu sütun adları)
        table_df = top_picks.iloc[3:].copy() # İlk 3 hariç kalanı al
        
        # Eğer hiç veri kalmadıysa (sadece 3 hisse varsa) tabloyu boş geçme, tümünü göster
        if table_df.empty: table_df = top_picks.copy()

        # Tabloyu düzenle
        display_df = table_df[[
            'Guven_Skoru_Num', 'Hisse', 'Karar', 'Fiyat', 'Hedef_Fiyat', 
            'Stop_Loss', 'Kasa_Yonetimi', 'Vade', 'Analiz_Ozeti'
        ]]
        
        display_df.columns = [
            'AI Puanı', 'Sembol', 'Trend', 'Giriş ($)', 'Hedef ($)', 
            'Stop ($)', 'Kasa %', 'Vade', 'AI Açıklaması'
        ]

        st.dataframe(
            display_df,
            column_config={
                "AI Puanı": st.column_config.ProgressColumn(
                    "AI Puanı", format="%d", min_value=0, max_value=100
                ),
                "AI Açıklaması": st.column_config.TextColumn("AI Açıklaması", width="large")
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )

    # =========================================================================
    # SEKME 2: PORTFÖY PLANLAYICI
    # =========================================================================
    with tab2:
        st.subheader("📊 Portföy Dağılım Önerisi")
        
        # Sadece "AL" veya "GÜÇLÜ AL" diyenleri filtrele
        buy_signals = df[df['Karar'].str.contains('AL', na=False)]
        
        if not buy_signals.empty:
            col_p1, col_p2 = st.columns([1, 2])
            
            with col_p1:
                st.info("💡 **Yapay Zeka Stratejisi:**\nAI, güven skoru yüksek olan hisselere portföyde yer verilmesini öneriyor. Aşağıdaki grafik, puanlarına göre ağırlık dağılımını gösterir.")
            
            with col_p2:
                # Basit bir Pasta Grafiği (Hisse vs Güven Skoru)
                chart = alt.Chart(buy_signals).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Guven_Skoru_Num", type="quantitative"),
                    color=alt.Color(field="Hisse", type="nominal"),
                    tooltip=["Hisse", "Guven_Skoru_Num", "Kasa_Yonetimi"]
                ).properties(title="Önerilen Portföy Ağırlıkları")
                st.altair_chart(chart, use_container_width=True)
                
            st.markdown("### 🗓️ Vade Planlaması")
            # Vade sürelerine göre grupla
            st.dataframe(
                buy_signals[['Hisse', 'Vade', 'Hedef_Fiyat', 'Stop_Loss']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning("Şu an 'AL' sinyali üreten güvenilir bir hisse bulunamadı.")

    # =========================================================================
    # SEKME 3: TÜM VERİLER (HAM)
    # =========================================================================
    with tab3:
        st.subheader("🗃️ Veritabanı Dökümü")
        st.text("Botun kaydettiği tüm ham veriler buradadır.")
        st.dataframe(df, use_container_width=True)
