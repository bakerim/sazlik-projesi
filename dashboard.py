import streamlit as st
import pandas as pd
import altair as alt
import time

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Projesi - Günlük Bülten",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. PROFESYONEL CSS TASARIMI ---
# (Buradaki tırnak işaretlerine dikkat et, hata buradan çıkıyor olabilir)
st.markdown("""
<style>
    .big-font { font-size: 24px !important; font-weight: bold; }
    .med-font { font-size: 18px !important; font-weight: bold; }
    .small-font { font-size: 14px !important; color: #888; }
    
    .score-green { color: #28a745; font-weight: bold; }
    .score-blue { color: #17a2b8; font-weight: bold; }
    .score-orange { color: #ffc107; font-weight: bold; }
    .score-grey { color: #6c757d; font-weight: bold; }

    .card-container {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-bottom: 15px;
    }
    .metric-box {
        background-color: #0d1117;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        border: 1px solid #21262d;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. VERİ YÜKLEME (HATASIZ) ---
@st.cache_data(ttl=300) # 5 dakikada bir önbellek temizle
def load_data():
    try:
        # CSV dosyasını güvenli modda oku
        df = pd.read_csv("sazlik_signals.csv", on_bad_lines='skip', engine='python')
        
        # Tarih formatını düzelt
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        
        # Sütunları kontrol et ve eksikleri tamamla (KeyError önlemi)
        required_cols = [
            'Hisse', 'Karar', 'Fiyat', 'Hedef_Fiyat', 'Stop_Loss', 
            'Guven_Skoru', 'Vade', 'Analiz_Ozeti', 'Kazanc_Potansiyeli', 
            'Risk_Yuzdesi', 'Kasa_Yonetimi', 'Link'
        ]
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0 if 'Fiyat' in col or 'Skor' in col else "-"

        # Her hisse için sadece EN GÜNCEL analizi al
        df = df.sort_values('Tarih', ascending=False).drop_duplicates('Hisse')
        
        return df
    except Exception as e:
        # Hata olursa logla ama boş tablo dön (Çökmeyi engeller)
        return pd.DataFrame()

# --- KRİTİK NOKTA: DEĞİŞKENİ BAŞLAT ---
df = pd.DataFrame() # Önce boş olarak tanımla
df = load_data()    # Sonra veriyi yüklemeye çalış

# --- RENK BELİRLEME ---
def get_score_class(score):
    try:
        s = int(score)
        if s >= 85: return "score-green"
        elif s >= 70: return "score-blue"
        elif s >= 60: return "score-orange"
        else: return "score-grey"
    except: return "score-grey"

# --- 4. ARAYÜZ (VİTRİN) ---
st.title("🌾 Sazlık Pro: Akıllı Analist")
st.markdown("---")

# Veri Kontrolü
if df.empty:
    st.info("📡 Veri bekleniyor... Botun çalışmasını bekleyin veya CSV dosyasını kontrol edin.")
    if st.button("Tekrar Dene"):
        st.rerun()
else:
    # SEKMELER
    tab1, tab2 = st.tabs(["🔥 VİTRİN (Öne Çıkanlar)", "📋 TÜM LİSTE (Detaylı)"])

    # --- TAB 1: KART GÖRÜNÜMÜ ---
    with tab1:
        # Güven Skoru sayısal değilse 0 kabul et
        df['Guven_Skoru_Num'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(0)
        
        # Sadece puanı 60 ve üzeri olanları göster
        top_picks = df[df['Guven_Skoru_Num'] >= 60]
        
        if top_picks.empty:
            st.warning("Şu an yüksek güvenli (60+) fırsat bulunamadı.")
        
        for index, row in top_picks.iterrows():
            score = int(row['Guven_Skoru_Num'])
            score_cls = get_score_class(score)
            karar = row.get('Karar', 'N/A')
            
            # Kart HTML Yapısı (F-string hatasız)
            st.markdown(f"""
            <div class="card-container">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:28px; font-weight:bold; color:white;">{row['Hisse']}</span>
                        <span style="background-color:#21262d; padding:5px 10px; border-radius:15px; margin-left:10px; border:1px solid #30363d;">
                            {karar}
                        </span>
                    </div>
                    <div style="text-align:right;">
                        <span class="{score_cls}" style="font-size:32px;">{score}</span>
                        <br><span style="font-size:12px; color:#888;">GÜVEN SKORU</span>
                    </div>
                </div>
                
                <hr style="border-color:#30363d; margin:15px 0;">
                
                <div style="display:flex; justify-content:space-between; text-align:center; gap:10px;">
                    <div class="metric-box" style="flex:1;">
                        <div class="small-font">HEDEF FİYAT</div>
                        <div class="med-font" style="color:#28a745;">${row.get('Hedef_Fiyat', 0)}</div>
                        <div style="font-size:12px; color:#28a745;">{row.get('Kazanc_Potansiyeli', '-')}</div>
                    </div>
                    <div class="metric-box" style="flex:1;">
                        <div class="small-font">STOP LOSS</div>
                        <div class="med-font" style="color:#dc3545;">${row.get('Stop_Loss', 0)}</div>
                        <div style="font-size:12px; color:#dc3545;">{row.get('Risk_Yuzdesi', '-')}</div>
                    </div>
                    <div class="metric-box" style="flex:1;">
                        <div class="small-font">VADE</div>
                        <div class="med-font" style="color:#e1e4e8;">{row.get('Vade', '-')}</div>
                    </div>
                    <div class="metric-box" style="flex:1;">
                        <div class="small-font">KASA</div>
                        <div class="med-font" style="color:#17a2b8;">{row.get('Kasa_Yonetimi', '-')}</div>
                    </div>
                </div>
                
                <div style="margin-top:15px; color:#c9d1d9; font-style:italic;">
                    " {row.get('Analiz_Ozeti', '')} "
                </div>
                <div style="margin-top:10px; font-size:12px; text-align:right;">
                    <a href="{row.get('Link', '#')}" target="_blank" style="color:#58a6ff;">Haber Kaynağı 🔗</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- TAB 2: TÜM LİSTE (Tablo) ---
    with tab2:
        # Tabloda gösterilecek sütunlar
        display_cols = ['Tarih', 'Hisse', 'Karar', 'Fiyat', 'Hedef_Fiyat', 'Stop_Loss', 'Guven_Skoru', 'Vade', 'Analiz_Ozeti']
        # Sütunların varlığını kontrol et
        valid_cols = [c for c in display_cols if c in df.columns]
        
        st.dataframe(
            df[valid_cols],
            use_container_width=True,
            height=600
        )
