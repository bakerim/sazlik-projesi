import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- ⚙️ SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Projesi - Komuta Merkezi",
    page_icon="🌾",
    layout="wide", # Geniş ekran modu (500 hisse için gerekli)
    initial_sidebar_state="expanded"
)

# --- 📂 VERİ YÜKLEME FONKSİYONLARI ---

@st.cache_data(ttl=60) # Her 60 saniyede bir veriyi tazele (Cache)
def load_analysis_data():
    """Analiz motorunun ürettiği CSV dosyasını okur."""
    file_path = "sazlik_analiz_sonuclari.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df
    return pd.DataFrame() # Dosya yoksa boş tablo dön

def load_news_data():
    """Haber botunun ürettiği JSON dosyasını okur."""
    file_path = "news_archive.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

# Verileri Yükle
df_analiz = load_analysis_data()
news_data = load_news_data()

# --- 🎨 ARAYÜZ (SIDEBAR - YAN MENÜ) ---
st.sidebar.title("🌾 Sazlık Paneli")
st.sidebar.markdown("---")

# Filtreleme Seçenekleri
st.sidebar.subheader("🔍 Filtreler")

# 1. Hisseler Listesi (CSV'den gelenler)
if not df_analiz.empty:
    all_tickers = df_analiz["Sembol"].unique().tolist()
    selected_ticker = st.sidebar.selectbox("Hisse Seç (Detay Analiz)", ["Tümü"] + all_tickers)
    
    # 2. Skor Filtresi
    min_score = st.sidebar.slider("Minimum Sazlık Skoru", 0, 100, 50)
else:
    selected_ticker = "Tümü"
    min_score = 0
    st.sidebar.warning("⚠️ Henüz analiz verisi (CSV) oluşmamış.")

st.sidebar.markdown("---")
st.sidebar.info("Botlar arka planda çalışırken bu sayfa verileri görselleştirir.")
if st.sidebar.button("🔄 Verileri Yenile"):
    st.rerun()

# --- 📊 ANA EKRAN ---

st.title("🌾 Sazlık Projesi: Yatırım Komuta Merkezi")
st.markdown(f"*Son Güncelleme: {datetime.now().strftime('%d-%m-%Y %H:%M')}*")

# Üst Bilgi Kartları (KPI)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Takip Edilen Hisse", len(df_analiz) if not df_analiz.empty else "0")
with col2:
    buy_signals = len(df_analiz[df_analiz["Sazlık_Skoru"] > 70]) if not df_analiz.empty else 0
    st.metric("🔥 Güçlü Al Sinyali", buy_signals)
with col3:
    st.metric("Arşivlenen Haber", len(news_data))
with col4:
    # İleride buraya 'Sentiment Ortalaması' gelecek
    st.metric("Piyasa Modu", "Nötr 😐") 

st.markdown("---")

# --- BÖLÜM 1: GÜÇLÜ FIRSATLAR TABLOSU (GEM FINDER) ---
st.subheader("💎 Öne Çıkan Fırsatlar (Sazlık Skoru Yüksek)")

if not df_analiz.empty:
    # Filtreleme Mantığı
    filtered_df = df_analiz[df_analiz["Sazlık_Skoru"] >= min_score]
    
    if selected_ticker != "Tümü":
        filtered_df = filtered_df[filtered_df["Sembol"] == selected_ticker]
    
    # Renkli ve Şık Tablo Gösterimi
    st.dataframe(
        filtered_df.style.background_gradient(subset=["Sazlık_Skoru"], cmap="RdYlGn"),
        use_container_width=True,
        height=300
    )
else:
    st.info("Analiz sonuçları bekleniyor... Lütfen 'analysis_engine.py' dosyasını çalıştırın.")

# --- BÖLÜM 2: HABER AKIŞI (NEWS FEED) ---
st.markdown("---")
st.subheader("📰 Son Dakika Haber Akışı")

# Haberleri Filtrele
filtered_news = news_data
if selected_ticker != "Tümü":
    filtered_news = [n for n in news_data if n['ticker'] == selected_ticker]

# Haberleri Ekrana Bas (Son 10 Haber)
if filtered_news:
    for news in filtered_news[:10]:
        with st.expander(f"📢 {news['ticker']} - {news['date']} | {news['content'][:80]}..."):
            st.markdown(f"**Başlık:** {news['content']}")
            st.markdown(f"[Haberi Oku 🔗]({news['link']})")
            st.caption(f"Yapay Zeka Yorumu: {news.get('ai_sentiment', 'Bekleniyor...')}")
else:
    st.write("Görüntülenecek haber yok.")

# --- ALT BİLGİ ---
st.markdown("---")
st.caption("Sazlık Projesi v1.0 | 500 Hisse Takip Sistemi | Powered by Python & Streamlit")
