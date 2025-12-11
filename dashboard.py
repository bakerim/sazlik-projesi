import streamlit as st
import pandas as pd
import altair as alt
import time
from datetime import datetime

# --- 1. SAYFA KONFİGÜRASYONU (Sazlık Klasik) ---
st.set_page_config(
    page_title="Sazlık Projesi - Terminal",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS STİL (Eski Tasarımın Havası) ---
st.markdown("""
<style>
    /* Metrik Kartları */
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 8px;
        color: #ddd;
    }
    /* Tablo Başlıkları */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    
    /* Genel Yazı Tipi */
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. VERİ YÜKLEME ---
@st.cache_data(ttl=60) # 60 saniyede bir önbellek temizle
def load_data():
    try:
        # CSV dosyasını oku
        df = pd.read_csv("sazlik_signals.csv")
        df['Tarih'] = pd.to_datetime(df['Tarih'])
        df = df.sort_values(by='Tarih', ascending=False)
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

# --- 4. KENAR ÇUBUĞU (SIDEBAR) ---
with st.sidebar:
    st.title("🌾 Sazlık Projesi")
    st.caption("v2.1 - Swing Trade Modülü")
    st.markdown("---")
    
    if not df.empty:
        # Filtreler
        st.subheader("🔍 Filtreleme")
        
        # Hisse Seçimi
        hisse_listesi = ["Tümü"] + sorted(list(df['Hisse'].unique()))
        secilen_hisse = st.selectbox("Hisse Senedi:", hisse_listesi)
        
        # Sinyal Seçimi
        sinyal_listesi = ["Tümü"] + sorted(list(df['Sinyal'].unique()))
        secilen_sinyal = st.selectbox("Sinyal Durumu:", sinyal_listesi)
        
        st.markdown("---")
        st.info(f"Son Güncelleme:\n{df['Tarih'].max().strftime('%d-%m-%Y %H:%M')}")
        
        if st.button("Verileri Yenile", type="primary"):
            st.rerun()
    else:
        st.warning("Veri bekleniyor...")

# --- VERİ FİLTRELEME MANTIĞI ---
if not df.empty:
    df_filtered = df.copy()
    if secilen_hisse != "Tümü":
        df_filtered = df_filtered[df_filtered['Hisse'] == secilen_hisse]
    if secilen_sinyal != "Tümü":
        df_filtered = df_filtered[df_filtered['Sinyal'] == secilen_sinyal]
else:
    df_filtered = pd.DataFrame()

# --- 5. ANA EKRAN (SEKMELİ YAPI) ---
st.header("📊 Piyasa İstihbarat Paneli")

# Sekmeleri Oluştur
tab1, tab2, tab3 = st.tabs(["⚡ Canlı Sinyaller", "📋 Detaylı Liste", "ℹ️ Sistem Durumu"])

# --- TAB 1: CANLI SİNYALLER (Görsel Ağırlıklı) ---
with tab1:
    if not df_filtered.empty:
        # Üst Metrikler
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Toplam Haber/Sinyal", len(df_filtered))
        
        # Al Sinyalleri
        al_sinyalleri = df_filtered[df_filtered['Sinyal'].str.contains("AL", case=False)]
        col2.metric("🟢 Al Fırsatları", len(al_sinyalleri))
        
        # Ortalama Değişim
        avg_change = df_filtered['Degisim_Yuzde'].mean()
        col3.metric("Ortalama Piyasa Yönü", f"%{avg_change:.2f}", delta_color="normal")
        
        # En Güçlü Hacim
        en_yuksek_hacim = df_filtered.loc[df_filtered['Hacim'].idxmax()]
        col4.metric("🔥 Hacim Lideri", en_yuksek_hacim['Hisse'], f"{en_yuksek_hacim['Hacim']:,}")

        st.markdown("---")
        
        # Grafikler
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Haber Duygusu ve Fiyat Tepkisi")
            chart = alt.Chart(df_filtered).mark_circle(size=100).encode(
                x=alt.X('Duygu_Skoru', title='Duygu (Negatif <-> Pozitif)'),
                y=alt.Y('Degisim_Yuzde', title='Fiyat Değişimi (%)'),
                color=alt.Color('Sinyal', scale={"scheme": "category10"}),
                tooltip=['Hisse', 'Fiyat', 'Sinyal', 'Haber_Baslik']
            ).properties(height=350).interactive()
            st.altair_chart(chart, use_container_width=True)
            
        with c2:
            st.subheader("Sinyal Dağılımı")
            pie_data = df_filtered['Sinyal'].value_counts().reset_index()
            pie_data.columns = ['Sinyal', 'Adet']
            
            bar_chart = alt.Chart(pie_data).mark_bar().encode(
                x='Adet',
                y=alt.Y('Sinyal', sort='-x'),
                color='Sinyal'
            ).properties(height=350)
            st.altair_chart(bar_chart, use_container_width=True)

    else:
        st.info("Görüntülenecek sinyal bulunamadı. Filtreleri kontrol edin veya botun çalışmasını bekleyin.")

# --- TAB 2: DETAYLI LİSTE (Excel Tarzı) ---
with tab2:
    if not df_filtered.empty:
        st.markdown("### 📝 Tüm İşlem Sinyalleri")
        
        # Tabloyu özelleştir (Gereksiz sütunları gizle)
        display_df = df_filtered[['Tarih', 'Hisse', 'Sinyal', 'Fiyat', 'Degisim_Yuzde', 'Haber_Baslik', 'Link']]
        
        # Renkli gösterim için stil fonksiyonu
        def highlight_signal(val):
            color = 'red' if 'SAT' in str(val) else 'green' if 'AL' in str(val) else 'white'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            display_df.style.applymap(highlight_signal, subset=['Sinyal'])
            .format({"Fiyat": "{:.2f} $", "Degisim_Yuzde": "%{:.2f}"}),
            use_container_width=True,
            height=600
        )
    else:
        st.warning("Veri yok.")

# --- TAB 3: SİSTEM BİLGİSİ ---
with tab3:
    st.markdown("### 🤖 Sazlık Bot İstatistikleri")
    col1, col2 = st.columns(2)
    with col1:
        st.success("Sistem: Çevrimiçi")
        st.write(f"**Takip Edilen Hisseler:** Apple, Microsoft, Nvidia, Tesla ve +30 Teknoloji Hissesi")
        st.write("**Veri Kaynağı:** Yahoo Finance & Global RSS Feeds")
    with col2:
        st.write("**Kullanılan Modeller:**")
        st.code("NLTK (VADER Sentiment Analysis)\nYfinance (Market Data)\nPandas (Data Processing)")
