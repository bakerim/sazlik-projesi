import streamlit as st
import pandas as pd
import altair as alt

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Pro - Terminal",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. PREMIUM CSS TASARIMI (BÜYÜK VE FERAH) ---
st.markdown("""
<style>
    /* Genel Arkaplan Ayarı */
    .stApp {
        background-color: #0d1117;
    }
    
    /* KART TASARIMI */
    .pro-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 25px; /* Daha fazla iç boşluk */
        margin-bottom: 25px; /* Kartlar arası boşluk */
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    
    /* HİSSE BAŞLIĞI */
    .ticker-header {
        font-size: 32px;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: 1px;
    }
    
    /* KARAR ETİKETLERİ */
    .badge {
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 16px;
        margin-left: 10px;
        vertical-align: middle;
    }
    .badge-buy { background-color: #238636; color: white; border: 1px solid #2ea043; }
    .badge-sell { background-color: #da3633; color: white; border: 1px solid #f85149; }
    .badge-wait { background-color: #9e6a03; color: white; border: 1px solid #d29922; }

    /* METRİK KUTULARI */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr); /* 4 Eşit Kolon */
        gap: 20px;
        margin-top: 20px;
        margin-bottom: 20px;
        padding: 15px;
        background-color: #0d1117; /* Kart içi koyu alan */
        border-radius: 8px;
        border: 1px solid #21262d;
    }
    
    .metric-item {
        text-align: center;
    }
    
    .metric-label {
        font-size: 13px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }
    
    .metric-value {
        font-size: 24px; /* Rakamlar artık kocaman */
        font-weight: bold;
        color: #e6edf3;
    }
    
    .metric-sub {
        font-size: 14px;
        font-weight: 500;
    }

    /* RENKLER */
    .text-green
