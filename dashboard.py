import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime
import time

# --- 1. SAYFA KONFİGÜRASYONU ---
st.set_page_config(
    page_title="Sazlık Projesi - AI Trade Terminali",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STİL VE RENKLER ---
st.markdown("""
<style>
    /* Kırmızı-Yeşil-Sarı renkler için özel stil */
    .metric-card {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 8px;
        color: #ddd;
    }
    .al-sinyali { color: #4CAF50; font-weight: bold; } /* Yeşil */
    .sat-sinyali { color: #F44336; font-weight: bold; } /* Kırmızı */
    .bekle-sinyali { color: #FFC107; font-weight: bold; } /* Sarı */
</style>
""", unsafe_allow_html=True)

# --- 3. VERİ YÜKLEME ---
@st.cache_data(ttl=30)
def load_data():
    try:
        # Hata olursa atlaması için error_bad_lines=False ve engine='python' ekliyoruz
        df = pd.read_csv("sazlik_signals.csv", on_bad_lines='skip', engine='python') # Buradaki satır DÜZELTİLDİ
        
        # Sütun isimlerini kontrol et (Bazen AI'dan gelen verideki sütunlar karışabilir)
        required_cols = ['Tarih', 'Hisse', 'Fiyat', 'Karar'] 
        if not all(col in df.columns for col in required_cols):
             st.error("CSV formatı bozuk: Gerekli sütunlar eksik.")
             return pd.DataFrame()
             
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        df = df.sort_values(by='Tarih', ascending=False)
        
        # ... (Diğer dönüşümlerin aynı kalması önemli)
        df['RSI'] = pd.to_numeric(df['RSI'], errors='coerce').fillna(0)
        df['Guven_Skoru'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(0).astype(int)

        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        # Genel bir hata olursa boş DataFrame dönsün
        st.error(f"Veri Yükleme Hatası: {e}")
        return pd.DataFrame()

# --- 4. KENAR ÇUBUĞU (SIDEBAR) ---
with st.sidebar:
    st.title("🤖 Sazlık AI Analist")
    st.caption("v3.0 - Gemini Destekli Stratejiler")
    st.markdown("---")
    
    if not df.empty:
        # Filtreler
        st.subheader("🔍 Filtreleme")
        hisse_listesi = ["Tümü"] + sorted(list(df['Hisse'].unique()))
        secilen_hisse = st.selectbox("Hisse Senedi:", hisse_listesi)
        
        karar_listesi = ["Tümü"] + sorted(list(df['Karar'].unique()))
        secilen_karar = st.selectbox("AI Kararı:", karar_listesi)
        
        # Filtreleme Mantığı
        df_filtered = df.copy()
        if secilen_hisse != "Tümü":
            df_filtered = df_filtered[df_filtered['Hisse'] == secilen_hisse]
        if secilen_karar != "Tümü":
            df_filtered = df_filtered[df_filtered['Karar'] == secilen_karar]

        st.markdown("---")
        st.info(f"Son Sinyal Tarihi:\n{df['Tarih'].max().strftime('%d-%m-%Y %H:%M')}")
        
        if st.button("Verileri Yenile", type="primary"):
            st.rerun()
    else:
        st.warning("Henüz AI sinyali yok. Botun çalışmasını bekleyin.")
        df_filtered = pd.DataFrame()

# --- 5. ANA EKRAN: GENEL BAKIŞ (TAB 1) ---
st.header("📊 AI Strateji Paneli")

if not df_filtered.empty:
    tab1, tab2 = st.tabs(["🚀 Yeni Trade Kurulumları", "📋 Detaylı Sinyal Geçmişi"])

    with tab1:
        st.subheader("En Güvenilir ve Yeni Trade Planları")
        
        # KPI'lar
        col1, col2, col3, col4 = st.columns(4)
        
        # En Yüksek Güven Skoru
        max_guven = df_filtered.loc[df_filtered['Guven_Skoru'].idxmax()]
        col1.metric("⭐ En Yüksek Güven", f"{max_guven['Guven_Skoru']}/100", max_guven['Hisse'])
        
        # En İyi Risk/Ödül
        risk_odul_series = df_filtered['Risk_Odul'].str.split(':', expand=True).iloc[:, 1]
        risk_odul_series = pd.to_numeric(risk_odul_series, errors='coerce').fillna(0)
        best_ro = df_filtered.loc[risk_odul_series.idxmax()]
        col2.metric("🏆 En İyi Risk/Ödül", best_ro['Risk_Odul'], best_ro['Hisse'])
        
        # Karar Dağılımı Grafiği
        karar_counts = df_filtered['Karar'].value_counts().reset_index()
        karar_counts.columns = ['Karar', 'Adet']
        
        chart = alt.Chart(karar_counts).mark_arc().encode(
            theta=alt.Theta(field="Adet", type="quantitative"),
            color=alt.Color(field="Karar", scale=alt.Scale(domain=['GÜÇLÜ AL', 'AL', 'BEKLE', 'SAT', 'GÜÇLÜ SAT'], 
                                                            range=['#4CAF50', '#A5D6A7', '#FFC107', '#F44336', '#E57373'])),
            tooltip=["Karar", "Adet"]
        ).properties(title="AI Karar Dağılımı")
        col3.altair_chart(chart, use_container_width=True)

        st.markdown("---")

        st.subheader("AI Analist Tarafından Önerilen Trade Setuplar:")
        
        # Her bir sinyali ayrı bir kartta göster
        for index, row in df_filtered.head(5).iterrows(): # Sadece en yeni 5 tanesini kart olarak göster
            karar_class = 'al-sinyali' if 'AL' in row['Karar'] else 'sat-sinyali' if 'SAT' in row['Karar'] else 'bekle-sinyali'
            
            with st.container():
                st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f"### <span class='{karar_class}'>🚀 {row['Karar']} Sinyali: {row['Hisse']}</span>", unsafe_allow_html=True)
                
                col_a, col_b, col_c, col_d = st.columns(4)
                
                col_a.metric("Giriş Fiyatı", f"${row['Fiyat']:.2f}")
                col_b.metric("🎯 Hedef Fiyat", f"${row['Hedef_Fiyat']:.2f}", row['Kazanc_Potansiyeli'])
                col_c.metric("🛑 Stop Loss", f"${row['Stop_Loss']:.2f}", row['Risk_Yuzdesi'])
                col_d.metric("📈 R/Ö Oranı", row['Risk_Odul'])
                
                st.caption(f"**Güven Skoru:** {row['Guven_Skoru']}/100 | **Kasa Yönetimi:** {row['Kasa_Yonetimi']}")
                st.markdown(f"**Özet:** *{row['Analiz_Ozeti']}*")
                st.markdown(f"**Haber:** {row['Haber_Baslik']} [Link]({row['Link']})")
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("---")
        
    # --- TAB 2: DETAYLI LİSTE ---
    with tab2:
        st.markdown("### 📋 Tüm AI Sinyal Geçmişi")
        
        # Renkli tablo stili
        def highlight_karar(val):
            if 'AL' in str(val):
                return 'background-color: #0E2A12; color: #4CAF50'
            elif 'SAT' in str(val):
                return 'background-color: #2A0E0E; color: #F44336'
            else:
                return 'background-color: #212121; color: #FFC107'

        display_df = df_filtered[[
            "Tarih", "Hisse", "Karar", "Fiyat", "Hedef_Fiyat", "Stop_Loss", "Guven_Skoru", "RSI", "Analiz_Ozeti", "Risk_Odul"
        ]]
        
        st.dataframe(
            display_df.style.applymap(highlight_karar, subset=['Karar'])
            .format({"Fiyat": "$ {:.2f}", "Hedef_Fiyat": "$ {:.2f}", "Stop_Loss": "$ {:.2f}", "RSI": "{:.2f}"}),
            use_container_width=True,
            height=600
        )

else:
    st.info("AI Analiz Sinyalleri bekleniyor...")
