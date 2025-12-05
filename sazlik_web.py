import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Sazlık: Fırsat Sıralaması", page_icon="🏆", layout="wide")

# --- API KONTROL ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı Yok! Streamlit Secrets ayarlarını yapmalısın.")
    st.stop()

# --- CSS TASARIMI ---
st.markdown("""
<style>
    .card {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .card:hover { transform: scale(1.02); }
    
    .score-badge {
        background: rgba(255,255,255,0.2);
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.1em;
        float: right;
    }
    
    .card-header { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .analysis-text { font-size: 15px; opacity: 0.9; margin-bottom: 15px; min-height: 60px; }
    
    .strategy-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 5px;
        background: rgba(0,0,0,0.25);
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
    .stat-label { font-size: 11px; color: #ccc; text-transform: uppercase; }
    .stat-val { font-size: 16px; font-weight: bold; }
    
    /* Renk Sınıfları */
    .tier-s { background: linear-gradient(135deg, #1b5e20 0%, #00e676 100%); border: 2px solid #00e676; }
    .tier-a { background: linear-gradient(135deg, #0d47a1 0%, #2979ff 100%); border: 2px solid #2979ff; }
    .tier-b { background: linear-gradient(135deg, #bf360c 0%, #ff6d00 100%); border: 2px solid #ff6d00; }
</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---

def get_technical_filter(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if hist.empty: return None
        
        price = hist['Close'].iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        
        # Trend kontrolü
        if price < sma20: return None 
        
        return {"price": price}
    except: return None

def get_news_leads():
    url = "https://raw.githubusercontent.com/bakerim/sazlik-projesi/main/news_archive.json"
    try:
        data = requests.get(url).json()
        leads = {}
        for item in data:
            ticker = item.get('ticker')
            if ticker not in leads: leads[ticker] = []
            leads[ticker].append(f"- {item['content']}")
        return leads
    except: return {}

def score_opportunity(ticker, tech_data, news_list):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    news_text = "\n".join(news_list[:3])
    
    prompt = f"""
    SEN "GARANTİCİ BABA" LAKAPLI TRADER'SIN.
    HİSSE: {ticker} | FİYAT: ${tech_data['price']:.2f} (Teknik: YÜKSELİŞ Trendi)
    HABERLER: {news_text}
    
    GÖREV: Swing trade fırsatına 0-100 arası GÜVEN PUANI ver.
    
    ÇIKTI (JSON):
    {{
        "puan": (Sayı),
        "baslik": "Kısa Başlık (Örn: ROKET HAZIRLIĞI)",
        "analiz": "Neden bu puanı verdin? (Maks 2 cümle)",
        "giris": {tech_data['price']:.2f},
        "hedef": (Kar al),
        "stop": (Stop noktası),
        "vade": "X Gün"
    }}
    """
    try:
        response = model.generate_content(prompt)
        # --- DÜZELTİLEN SATIR BURASI ---
        text = response.text.replace('```json', '').replace('```', '')
        # -------------------------------
        return json.loads(text)
    except: return None

# --- ARAYÜZ ---
st.title("🏆 Sazlık: Fırsat Sıralaması")
st.markdown("---")

if st.button("LİDERLİK TABLOSUNU OLUŞTUR 📊", type="primary"):
    
    news_dict = get_news_leads()
    
    if not news_dict:
        st.warning("Bot henüz veri toplamamış.")
    else:
        status_text = st.empty()
        bar = st.progress(0)
        
        tickers = list(news_dict.keys())
        scanned_results = []
        
        for i, ticker in enumerate(tickers):
            status_text.text(f"Analiz ediliyor: {ticker}...")
            bar.progress((i + 1) / len(tickers))
            
            tech = get_technical_filter(ticker)
            if not tech: continue
            
            ai_res = score_opportunity(ticker, tech, news_dict[ticker])
            
            # 60 Puan Barajı
            if ai_res and ai_res['puan'] >= 60:
                ai_res['ticker'] = ticker
                ai_res['news'] = news_dict[ticker]
                scanned_results.append(ai_res)
        
        status_text.empty()
        bar.empty()
        
        # SIRALAMA
        scanned_results.sort(key=lambda x: x['puan'], reverse=True)
        
        if not scanned_results:
            st.info("Trendi pozitif olup geçer not (60+) alan hisse çıkmadı.")
        else:
            st.success(f"Toplam {len(scanned_results)} fırsat bulundu!")
            
            for res in scanned_results:
                puan = res['puan']
                if puan >= 90:
                    css_class = "tier-s"
                    icon = "💎"
                elif puan >= 75:
                    css_class = "tier-a"
                    icon = "🔥"
                else:
                    css_class = "tier-b"
                    icon = "⚠️"
                
                st.markdown(f"""
                <div class="card {css_class}">
                    <div class="card-header">
                        {icon} {res['ticker']}: {res['baslik']}
                        <div class="score-badge">PUAN: {puan}</div>
                    </div>
                    <div class="analysis-text">{res['analiz']}</div>
                    <div class="strategy-grid">
                        <div><div class="stat-label">GİRİŞ</div><div class="stat-val">${res['giris']}</div></div>
                        <div><div class="stat-label">HEDEF</div><div class="stat-val">${res['hedef']}</div></div>
                        <div><div class="stat-label">STOP</div><div class="stat-val">${res['stop']}</div></div>
                        <div><div class="stat-label">VADE</div><div class="stat-val">{res['vade']}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"Haber Detayları"):
                    st.text("\n".join(res['news'][:3]))
