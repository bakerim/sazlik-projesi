import streamlit as st
import news_bot
from datetime import datetime

st.set_page_config(page_title="Sazlık İkili Masa", layout="wide")

# --- CSS TASARIM ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; margin-bottom: 10px;
    }
    div[data-testid="stMetricValue"] { font-size: 16px !important; color: #fff !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 11px !important; color: #8b949e !important; }
    .header-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 20px; color: white; margin-bottom: 15px; }
    .guven-h { background: linear-gradient(90deg, #1565c0, #0d47a1); }
    .firsat-h { background: linear-gradient(90deg, #c62828, #b71c1c); }
</style>
""", unsafe_allow_html=True)

st.title("🦅 SAZLIK PRO - V3 (HACİM MOTORLU)")

# --- BUTON VE DURUM ---
if st.button("🚀 PİYASA TARAMASINI BAŞLAT", type="primary", use_container_width=True):
    with st.spinner("Hisseler ve Hacimler Analiz Ediliyor..."):
        try:
            g, f = news_bot.run_analysis_engine()
            st.session_state.guven = g
            st.session_state.firsat = f
            st.session_state.last_update = datetime.now().strftime("%H:%M")
        except Exception as e:
            st.error(f"Motor Hatası: {e}")

# --- SONUÇLAR ---
if 'guven' in st.session_state and 'firsat' in st.session_state:
    st.caption(f"Son Güncelleme: {st.session_state.last_update}")
    m1, m2 = st.columns(2)
    
    # === SOL MASA: GÜVEN ===
    with m1:
        st.markdown('<div class="header-box guven-h">🛡️ GÜVEN MASASI (İstikrar)</div>', unsafe_allow_html=True)
        if not st.session_state.guven: st.info("Uygun aday yok.")
        for res in st.session_state.guven:
            with st.container(border=True):
                c1, c2 = st.columns([2,1])
                c1.subheader(f"{res['Hisse']}")
                # Hacim Rozeti
                vol = res.get('Vol_Signal', '-')
                color = "green" if "🔥" in vol else "orange" if "⚠️" in vol else "blue"
                c2.markdown(f":{color}[**{vol}**]")
                
                t1, t2, t3 = st.columns(3)
                t1.metric("PUAN", f"{res.get('Guven_Puan',0):.0f}")
                t2.metric("R²", f"{res.get('R2',0):.2f}")
                t3.metric("Eğim", f"{res.get('Slope',0):.2f}")
                
                p1, p2, p3 = st.columns(3)
                p1.metric("GİRİŞ", f"${res['Fiyat']:.2f}")
                p2.metric("HEDEF", f"${res.get('Hedef_G',0):.2f}")
                p3.metric("STOP", f"${res.get('Stop_G',0):.2f}")
                
                kar = res.get('Hedef_G',0) - res['Fiyat']
                yuzde = (kar / res['Fiyat']) * 100
                st.info(f"📈 Potansiyel: +${kar:.2f} (%{yuzde:.2f})")

    # === SAĞ MASA: FIRSAT ===
    with m2:
        st.markdown('<div class="header-box firsat-h">⚡ FIRSAT MASASI (Scalp)</div>', unsafe_allow_html=True)
        if not st.session_state.firsat: st.info("Fırsat yok.")
        for res in st.session_state.firsat:
            with st.container(border=True):
                c1, c2 = st.columns([2,1])
                c1.subheader(f"{res['Hisse']}")
                vol = res.get('Vol_Signal', '-')
                color = "green" if "🔥" in vol else "orange" if "⚠️" in vol else "blue"
                c2.markdown(f":{color}[**{vol}**]")
                
                t1, t2, t3 = st.columns(3)
                t1.metric("PUAN", f"{res.get('Firsat_Puan',0):.0f}")
                t2.metric("HIZ/GÜN", f"%{res.get('Hiz_Pct',0):.2f}")
                t3.metric("VADE", res.get('Vade','-'))
                
                p1, p2, p3 = st.columns(3)
                p1.metric("GİRİŞ", f"${res['Fiyat']:.2f}")
                p2.metric("HEDEF (+5%)", f"${res.get('Hedef_F',0):.2f}")
                p3.metric("STOP (-3%)", f"${res.get('Stop_F',0):.2f}")
                
                st.button(f"⚡ {res['Hisse']} İÇİN VUR-KAÇ", key=f"btn_{res['Hisse']}", type="primary", use_container_width=True)