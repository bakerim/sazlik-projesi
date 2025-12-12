import streamlit as st
import pandas as pd
import altair as alt

# --- AYARLAR ---
st.set_page_config(page_title="Sazlık Pro v4", layout="wide", initial_sidebar_state="collapsed")

# --- CSS TASARIMI (BÜYÜK RAKAMLAR & RENKLER) ---
st.markdown("""
<style>
    .big-font { font-size: 24px !important; font-weight: bold; }
    .med-font { font-size: 18px !important; font-weight: bold; }
    .small-font { font-size: 14px !important; color: #888; }
    
    /* SKOR RENKLERİ */
    .score-green { color: #28a745; font-weight: bold; } /* 85-100 */
    .score-blue { color: #17a2b8; font-weight: bold; }  /* 70-84 */
    .score-orange { color: #ffc107; font-weight: bold; } /* 60-69 */
    .score-grey { color: #6c757d; font-weight: bold; }   /* <60 */

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

# --- VERİ YÜKLEME ---
def load_data():
    try:
        df = pd.read_csv("sazlik_signals.csv")
        df['Tarih'] = pd.to_datetime(df['Tarih'])
        # EN ÖNEMLİ KISIM: Her hisse için sadece EN SON analizi al
        df = df.sort_values('Tarih', ascending=False).drop_duplicates('Hisse')
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- RENK BELİRLEME FONKSİYONU ---
def get_score_class(score):
    try:
        s = int(score)
        if s >= 85: return "score-green" # Yeşil
        elif s >= 70: return "score-blue"  # Mavi
        elif s >= 60: return "score-orange" # Turuncu
        else: return "score-grey"
    except: return "score-grey"

# --- ARAYÜZ ---
st.title("🌾 Sazlık Pro: Akıllı Analist")
st.markdown("---")

if df.empty:
    st.warning("Henüz veri yok. Botun çalışmasını bekleyin.")
else:
    # SEKMELER
    tab1, tab2 = st.tabs(["🔥 VİTRİN (Öne Çıkanlar)", "📋 TÜM LİSTE (Detaylı)"])

    # --- TAB 1: KART GÖRÜNÜMÜ ---
    with tab1:
        # Sadece puanı 60 üstü olanları vitrine koyalım
        top_picks = df[pd.to_numeric(df['Guven_Skoru'], errors='coerce') >= 60]
        
        for index, row in top_picks.iterrows():
            score = row.get('Guven_Skoru', 0)
            score_cls = get_score_class(score)
            karar = row.get('Karar', 'N/A')
            
            # Kart HTML Yapısı
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
        st.dataframe(
            df[['Tarih', 'Hisse', 'Karar', 'Fiyat', 'Hedef_Fiyat', 'Stop_Loss', 'Guven_Skoru', 'Vade', 'Analiz_Ozeti']],
            use_container_width=True,
            height=600
        )
