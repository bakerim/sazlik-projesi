import streamlit as st
import pandas as pd
import altair as alt
import time

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Projesi - Günlük Bülten",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed" # Daha geniş ekran için menüyü kapalı başlatıyoruz
)

# --- 2. PROFESYONEL CSS TASARIMI (BÜLTEN TARZI) ---
st.markdown("""
<style>
    /* Kart Tasarımı */
    div.css-1r6slb0.e1tzin5v2 {
        background-color: #0E1117;
        border: 1px solid #30333F;
    }
    .metric-card {
        background-color: #161b22; /* Koyu Gri/Siyah */
        border-left: 5px solid #238636; /* Sol tarafta Yeşil Çizgi */
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .metric-card-sell {
        background-color: #161b22;
        border-left: 5px solid #da3633; /* Sol tarafta Kırmızı Çizgi */
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .card-title {
        font-size: 20px;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 10px;
    }
    .card-metric-label {
        font-size: 12px;
        color: #8b949e;
    }
    .card-metric-value {
        font-size: 18px;
        font-weight: bold;
        color: #e6edf3;
    }
    .success-text { color: #3fb950; }
    .danger-text { color: #f85149; }
    
    /* Tablo Başlıklarını Gizle/Düzenle */
    thead tr th:first-child {display:none}
    tbody th {display:none}
</style>
""", unsafe_allow_html=True)

# --- 3. GÜVENLİ VERİ YÜKLEME ---
@st.cache_data(ttl=30)
def load_data():
    try:
        # Hata korumalı okuma
        df = pd.read_csv("sazlik_signals.csv", on_bad_lines='skip', engine='python')
        
        # Tarih formatı
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        df = df.sort_values(by='Tarih', ascending=False)
        
        # KRİTİK: Eksik sütunları doldur (KeyError önleyici)
        expected_cols = ['Stop_Loss', 'Hedef_Fiyat', 'Risk_Yuzdesi', 'Kazanc_Potansiyeli', 'Risk_Odul', 'Guven_Skoru']
        for col in expected_cols:
            if col not in df.columns:
                df[col] = 0 # Veya uygun bir varsayılan değer
        
        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Veri okunurken hata: {e}")
        return pd.DataFrame()

# Veriyi Yükle
df = load_data()

# --- 4. ÜST BAŞLIK VE ÖZET ---
st.title("🌾 Sazlık Projesi: Günlük Bülten")
st.markdown("Yapay Zeka Destekli Swing Trade Sinyalleri ve Piyasa Analizi")
st.markdown("---")

# --- 5. ANA EKRAN MANTIĞI ---
if not df.empty:
    
    # --- BÖLÜM 1: YAPAY ZEKA'NIN GÖZÜNE ÇARPANLAR (KARTLAR) ---
    st.subheader("🤖 Yapay Zeka'nın Gözüne Çarpanlar (Top Picks)")
    st.caption("Sistem, Güven Skoru ve Risk/Ödül oranına göre en iyi fırsatları öne çıkarır.")
    
    # En iyi 3 sinyali seç (Güven Skoruna göre)
    # Önce sayısal dönüşüm garantisi
    df['Guven_Skoru'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(0)
    top_picks = df.sort_values(by='Guven_Skoru', ascending=False).head(3)
    
    cols = st.columns(3) # 3 Yan yana kart
    
    for i, (index, row) in enumerate(top_picks.iterrows()):
        # Kart rengini karara göre belirle
        card_class = "metric-card" if "AL" in str(row.get('Karar')) else "metric-card-sell"
        trend_icon = "🟢" if "AL" in str(row.get('Karar')) else "🔴"
        col = cols[i % 3]
        
        with col:
            st.markdown(f"""
            <div class="{card_class}">
                <div class="card-title">{trend_icon} #{i+1} {row.get('Hisse', 'N/A')}</div>
                <div style="margin-bottom: 10px; font-size: 14px;"><i>{row.get('Karar', '-')}</i></div>
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <div class="card-metric-label">HEDEF</div>
                        <div class="card-metric-value success-text">${row.get('Hedef_Fiyat', 0):.2f}</div>
                        <div style="font-size: 11px; color: #3fb950;">{row.get('Kazanc_Potansiyeli', '-')}</div>
                    </div>
                    <div>
                        <div class="card-metric-label">GİRİŞ</div>
                        <div class="card-metric-value">${row.get('Fiyat', 0):.2f}</div>
                    </div>
                    <div>
                        <div class="card-metric-label">STOP</div>
                        <div class="card-metric-value danger-text">${row.get('Stop_Loss', 0):.2f}</div>
                        <div style="font-size: 11px; color: #f85149;">{row.get('Risk_Yuzdesi', '-')}</div>
                    </div>
                </div>
                <hr style="border-color: #30333F; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #8b949e;">
                    <span>Risk/Ödül: <b>{row.get('Risk_Odul', '-')}</b></span>
                    <span>Güven: <b>{int(row.get('Guven_Skoru', 0))}/100</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- BÖLÜM 2: DETAYLI LİSTE (Tablo Görünümü) ---
    st.markdown("### 📋 Listenin Devamı (Detaylı Analiz)")
    
    # Tablo için temiz veri
    display_df = df[[
        'Hisse', 'Karar', 'Fiyat', 'Hedef_Fiyat', 'Stop_Loss', 
        'Risk_Odul', 'Guven_Skoru', 'Analiz_Ozeti', 'Haber_Baslik'
    ]].copy()
    
    # Tablo Renklendirme Fonksiyonu
    def color_coding(val):
        color = '#ffffff' # Varsayılan beyaz
        if 'AL' in str(val): color = '#3fb950' # Yeşil
        elif 'SAT' in str(val): color = '#f85149' # Kırmızı
        elif 'BEKLE' in str(val): color = '#e3b341' # Sarı
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        display_df.style.applymap(color_coding, subset=['Karar'])
        .format({
            "Fiyat": "${:.2f}", 
            "Hedef_Fiyat": "${:.2f}", 
            "Stop_Loss": "${:.2f}",
            "Guven_Skoru": "{:.0f}"
        }),
        use_container_width=True,
        height=500
    )
    
    # Yenileme Butonu
    if st.button("🔄 Verileri Yenile"):
        st.rerun()

else:
    # Veri yoksa gösterilecek şık uyarı
    st.info("📡 Veri bekleniyor... Bot piyasayı tarıyor.")
    if st.button("Şimdi Kontrol Et"):
        st.rerun()

# --- 6. SIDEBAR (FİLTRELER) ---
with st.sidebar:
    st.header("🔍 Filtreleme")
    if not df.empty:
        hisse_sec = st.selectbox("Hisse Seç:", ["Tümü"] + list(df['Hisse'].unique()))
        if hisse_sec != "Tümü":
            st.warning(f"Sadece {hisse_sec} gösteriliyor (Yukarıdaki tablo filtrelenmedi, sadece kartlar güncellenecek)")
