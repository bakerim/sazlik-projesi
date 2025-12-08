import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- ⚙️ SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Projesi | AI Analyst",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS (MODERN SUNUM TARZI) ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #0e1117;
        border-radius: 5px;
        color: white;
        border: 1px solid #30333d;
    }
    .stTabs [aria-selected="true"] {
        background-color: #262730;
        border-color: #4CAF50;
        color: #4CAF50;
    }
    .metric-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 10px;
    }
    .profit-tag { color: #4CAF50; font-size: 0.9em; font-weight: bold; }
    .loss-tag { color: #ff4b4b; font-size: 0.9em; font-weight: bold; }
    h2, h3, p { margin: 0; padding: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 📂 VERİ YÜKLEME ---
@st.cache_data(ttl=60)
def load_data():
    df = pd.DataFrame()
    news = []
    
    # Analiz Verisi
    if os.path.exists("sazlik_swing_data.csv"):
        df = pd.read_csv("sazlik_swing_data.csv")
    
    # Haber Verisi
    if os.path.exists("news_archive.json"):
        with open("news_archive.json", "r") as f:
            news = json.load(f)
            
    return df, news

df, news_data = load_data()

# --- 🧠 YAPAY ZEKA SIRALAMA ALGORİTMASI ---
def get_ai_top_picks(dataframe, limit=10):
    if dataframe.empty: return dataframe
    
    df_scored = dataframe.copy()
    # Puanlama Algoritması
    df_scored['AI_SCORE'] = df_scored['R/R'] * 10
    df_scored.loc[df_scored['TREND'] == 'Yükseliş', 'AI_SCORE'] += 20
    df_scored.loc[df_scored['VADE'].str.contains('Kısa'), 'AI_SCORE'] += 5
    df_scored = df_scored[df_scored['R/R'] > 1.0]
    
    return df_scored.sort_values(by='AI_SCORE', ascending=False).head(limit)

# --- 🎨 HTML KART OLUŞTURUCU (HATA ÖNLEYİCİ - SOLA YAPIŞIK) ---
def create_card_html(rank, item):
    """HTML kodunu temiz bir şekilde oluşturur."""
    
    kar_yuzdesi = ((item['HEDEF'] - item['GİRİŞ']) / item['GİRİŞ']) * 100
    zarar_yuzdesi = ((item['GİRİŞ'] - item['STOP']) / item['GİRİŞ']) * 100
    
    # NOT: HTML kodları bilerek en sola yaslanmıştır. 
    # Streamlit girinti görürse kod bloğu sanıyor.
    html_content = f"""
<div class="metric-card">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
<h2 style="margin:0; color:#4CAF50; font-size:24px;">#{rank} {item['SEMBL']}</h2>
<span style="background:#262730; padding:4px 10px; border-radius:4px; font-size:12px; border:1px solid #444;">{item['TREND']}</span>
</div>
<p style="font-size:14px; color:#aaa; margin-bottom:10px;">⏱️ Vade: {item['VADE']}</p>
<div style="background:#21262d; padding:10px; border-radius:6px; margin-bottom:10px;">
<span style="color:#8b949e; font-size:12px; text-transform:uppercase;">Hedef Fiyat</span><br>
<span style="font-size:22px; font-weight:bold; color:#e6edf3;">${item['HEDEF']}</span>
<span class="profit-tag"> (▲ %{kar_yuzdesi:.2f})</span>
</div>
<div style="display:flex; justify-content:space-between; gap:10px;">
<div style="flex:1; background:#21262d; padding:8px; border-radius:6px;">
<span style="color:#8b949e; font-size:11px;">GİRİŞ</span><br>
<strong style="color:#e6edf3;">${item['GİRİŞ']}</strong>
</div>
<div style="flex:1; background:#21262d; padding:8px; border-radius:6px;">
<span style="color:#8b949e; font-size:11px;">STOP</span><br>
<strong style="color:#e6edf3;">${item['STOP']}</strong> 
<br><span class="loss-tag" style="font-size:11px;">(▼ %{zarar_yuzdesi:.2f})</span>
</div>
</div>
<div style="margin-top:12px; text-align:center; padding-top:8px; border-top:1px solid #30363d;">
<small style="color:#8b949e;">Risk/Ödül Oranı: <strong style="color:#fff;">{item['R/R']}</strong></small>
</div>
</div>
"""
    return html_content

# --- 🖥️ ARAYÜZ ---

st.title("🌾 Sazlık Projesi: Günlük Bülten")
st.caption(f"📅 {datetime.now().strftime('%d %B %Y')} | Analiz Edilen Hisse: {len(df)}")

# Sekmeler
tab1, tab2, tab3 = st.tabs(["🏆 AI Seçkisi (Top 10)", "💰 Portföy Planlayıcı", "🔬 Tüm Veriler"])

# --- TAB 1: AI SUNUMU (GÜNÜN FIRSATLARI) ---
with tab1:
    st.markdown("### 🤖 Yapay Zeka'nın Gözüne Çarpanlar")
    st.markdown("Sistem, 500 hisse arasından **R/R oranı en yüksek** ve **Trendi Pozitif** olanları ayıkladı.")
    
    top_picks = get_ai_top_picks(df, limit=10)
    
    if not top_picks.empty:
        # --- KART GÖRÜNÜMÜ (TOP 3) ---
        col1, col2, col3 = st.columns(3)
        top_3 = top_picks.head(3).to_dict('records')
        
        for i, col in enumerate([col1, col2, col3]):
            if i < len(top_3):
                item = top_3[i]
                # HTML fonksiyonunu çağırıyoruz
                card_html = create_card_html(i+1, item)
                with col:
                    st.markdown(card_html, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 📋 Listenin Devamı (Detaylı Analiz)")
        
        # Tablo Gösterimi
        display_picks = top_picks.copy()
        display_picks['KAR POT. (%)'] = ((display_picks['HEDEF'] - display_picks['GİRİŞ']) / display_picks['GİRİŞ']) * 100
        display_picks['RİSK (%)'] = ((display_picks['GİRİŞ'] - display_picks['STOP']) / display_picks['GİRİŞ']) * 100
        
        cols_to_show = ["SEMBL", "GÜNCEL", "R/R", "TREND", "KAR POT. (%)", "RİSK (%)", "GİRİŞ", "HEDEF", "STOP"]
        
        st.dataframe(
            display_picks[cols_to_show].style
            .background_gradient(subset=["R/R"], cmap="Greens")
            .format({
                "GÜNCEL": "${:.2f}", "GİRİŞ": "${:.2f}", "HEDEF": "${:.2f}", "STOP": "${:.2f}",
                "KAR POT. (%)": "%{:.2f}", "RİSK (%)": "%{:.2f}"
            }),
            use_container_width=True,
            hide_index=True
        )
        
    else:
        st.warning("⚠️ Kriterlere uygun 'Güçlü Al' fırsatı bulunamadı. Piyasa yatay veya düşüşte olabilir.")

# --- TAB 2: PORTFÖY PLANLAYICI (KASA) ---
with tab2:
    st.markdown("### 💼 Kasa Yönetimi Simülasyonu")
    
    col_kasa, col_risk = st.columns(2)
    with col_kasa:
        kasa = st.number_input("Toplam Kasa ($)", value=10000, step=1000)
    with col_risk:
        risk_pct = st.slider("İşlem Başı Risk (%)", 1, 5, 2)
    
    if not top_picks.empty:
        sim_df = top_picks.copy()
        
        def calc_lot(row):
            risk_per_share = row['GİRİŞ'] - row['STOP']
            if risk_per_share <= 0: return 0
            max_risk_amt = kasa * (risk_pct / 100)
            return int(max_risk_amt / risk_per_share)
            
        sim_df['LOT'] = sim_df.apply(calc_lot, axis=1)
        sim_df['YATIRIM ($)'] = sim_df['LOT'] * sim_df['GİRİŞ']
        sim_df['POT. KAZANÇ ($)'] = sim_df['LOT'] * (sim_df['HEDEF'] - sim_df['GİRİŞ'])
        
        sim_df = sim_df[sim_df['LOT'] > 0]
        
        total_inv = sim_df['YATIRIM ($)'].sum()
        total_prof = sim_df['POT. KAZANÇ ($)'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Gerekli Sermaye", f"${total_inv:,.2f}")
        c2.metric("Top 10 Hedef Kazanç", f"${total_prof:,.2f}", delta=f"%{(total_prof/total_inv)*100:.1f} Getiri" if total_inv>0 else "0")
        
        st.dataframe(
            sim_df[["SEMBL", "LOT", "YATIRIM ($)", "POT. KAZANÇ ($)", "R/R"]].style.format("${:.2f}", subset=["YATIRIM ($)", "POT. KAZANÇ ($)"]),
            use_container_width=True
        )
    else:
        st.info("Top 10 listesi boş olduğu için hesaplama yapılamadı.")

# --- TAB 3: TÜM VERİLER ---
with tab3:
    st.markdown("### 🔬 Detaylı Veri Havuzu")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        search = st.text_input("Hisse Ara (Örn: AAPL)", "")
    with col_f2:
        trend_select = st.selectbox("Trend Filtresi", ["Tümü", "Yükseliş", "Düşüş"])
        
    filtered_full = df.copy()
    if search:
        filtered_full = filtered_full[filtered_full['SEMBL'].str.contains(search.upper())]
    if trend_select != "Tümü":
        filtered_full = filtered_full[filtered_full['TREND'] == trend_select]
        
    st.dataframe(filtered_full, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📰 İlgili Haberler (Son 30 Gün)")
    
    if news_data:
        for news in news_data[:20]: 
            sentiment = news.get('ai_sentiment', 'Nötr')
            icon = "🟢" if "Olumlu" in sentiment else "🔴" if "Olumsuz" in sentiment else "⚪"
            
            with st.expander(f"{icon} {news['ticker']} - {news['date']}"):
                st.write(news['content'])
                st.caption(f"Yapay Zeka Yorumu: {sentiment}")
                st.markdown(f"[Habere Git]({news['link']})")
    else:
        st.write("Arşivlenmiş haber bulunamadı.")

# --- FOOTER ---
st.markdown("---")
st.caption("Sazlık Projesi v2.4 | AI Powered Swing Trading System")