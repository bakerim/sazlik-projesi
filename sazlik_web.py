import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Sazlık Pro: Şüpheci Mod", page_icon="🛡️", layout="wide")

# --- API KONTROL ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı Yok!")
    st.stop()

# --- 100 HİSSELİK LİSTE ---
WATCHLIST = [
    'NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'AMD', 'INTC',
    'PLTR', 'AI', 'SMCI', 'ARM', 'PATH', 'SNOW', 'CRWD', 'PANW', 'ORCL', 'ADBE',
    'COIN', 'MSTR', 'MARA', 'RIOT', 'HOOD', 'PYPL', 'SQ', 'V', 'MA', 'JPM',
    'RIVN', 'LCID', 'NIO', 'FSLR', 'ENPH', 'XOM', 'CVX',
    'WMT', 'COST', 'TGT', 'DIS', 'BA', 'LMT', 'GE', 'PFE', 'LLY', 'NVO',
    'BABA', 'PDD', 'BIDU', 'JD', 'CSCO', 'TXN', 'AVGO', 'MU', 'LRCX', 'AMAT',
    'DDOG', 'ZS', 'NET', 'MDB', 'TEAM', 'U', 'DKNG', 'ROKU', 'SHOP',
    'CLSK', 'HUT', 'BITF', 'XPEV', 'LI', 'SEDG', 'PLUG', 'FCEL',
    'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'AXP',
    'HD', 'LOW', 'NKE', 'LULU', 'SBUX', 'MCD', 'KO',
    'MRNA', 'BNTX', 'VRTX', 'REGN', 'GILD', 'AMGN', 'ISRG',
    'RTX', 'CAT', 'DE', 'HON', 'UNP', 'UPS', 'FDX', 'CMCSA', 'TMUS', 'VZ', 'T', 'F', 'GM', 'UBER', 'ABNB', 'DASH'
]
WATCHLIST.sort()

# --- CSS TASARIMI ---
st.markdown("""
<style>
    .card {
        padding: 20px; border-radius: 15px; margin-bottom: 20px; color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .score-badge {
        background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px; font-weight: 800; float: right;
    }
    .card-header { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .analysis-text { font-size: 15px; opacity: 0.9; margin-bottom: 15px; }
    
    .strategy-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 5px; background: rgba(0,0,0,0.25); padding: 10px; border-radius: 10px; text-align: center;
    }
    .risk-row {
        background-color: #3b3b3b;
        padding: 8px;
        border-radius: 8px;
        margin-top: 10px;
        display: flex;
        justify-content: space-around;
        font-weight: bold;
    }
    .stat-label { font-size: 11px; color: #ccc; text-transform: uppercase; }
    .stat-val { font-size: 16px; font-weight: bold; }
    
    .tier-s { background: linear-gradient(135deg, #1b5e20 0%, #00e676 100%); border: 2px solid #00e676; }
    .tier-a { background: linear-gradient(135deg, #0d47a1 0%, #2979ff 100%); border: 2px solid #2979ff; }
    .tier-b { background: linear-gradient(135deg, #bf360c 0%, #ff6d00 100%); border: 2px solid #ff6d00; }
    .tier-fail { background: #424242; border: 1px solid #757575; opacity: 0.6; }
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
        trend_durumu = "POZİTİF" if price > sma20 else "NEGATİF"
        return {"price": price, "trend": trend_durumu}
    except: return None

def get_news_leads():
    url = "https://raw.githubusercontent.com/bakerim/sazlik-projesi/main/news_archive.json"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        leads = {}
        for item in data:
            ticker = item.get('ticker')
            if ticker:
                if ticker not in leads: leads[ticker] = []
                leads[ticker].append(f"- {item['content']}")
        return leads
    except: return {}

def score_opportunity(ticker, tech_data, news_list):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    news_text = "\n".join(news_list[:3]) if news_list else "Haber yok."
    
    # --- ŞÜPHECİ PROMPT ---
    prompt = f"""
    SEN "GARANTİCİ BABA" LAKAPLI, ŞÜPHECİ BİR TRADER'SIN.
    HİSSE: {ticker} | FİYAT: ${tech_data['price']:.2f} | TREND: {tech_data['trend']}
    HABERLER: {news_text}
    
    KURALLAR:
    1. Haber metninde "{ticker}" yoksa veya alakasızsa PUANI SIFIRLA.
    2. Trend NEGATİF ise puanı 45'in altına çek.
    3. RİSK/KAZANÇ (R/R) oranını hesapla (Örn: 1:3).
    
    ÇIKTI (JSON):
    {{
        "puan": (0-100 arası sayı),
        "baslik": "Kısa Başlık",
        "analiz": "Analiz yorumu",
        "giris": {tech_data['price']:.2f},
        "hedef": (Hedef),
        "stop": (Stop),
        "vade": "X Gün",
        "rr_orani": "1:X",
        "kasa_yuzdesi": "%X"
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '')
        return json.loads(text)
    except: return None

# --- KART GÖSTERİMİ (DÜZELTİLMİŞ) ---
def display_card(res):
    puan = res['puan']
    
    if puan >= 90: c, i = "tier-s", "💎"
    elif puan >= 80: c, i = "tier-a", "🔥"
    elif puan >= 60: c, i = "tier-b", "⚠️"
    else: c, i = "tier-fail", "⛔"

    # HTML KODUNU DUVARA YAPIŞTIRDIK (Boşluk yok!)
    html_card = f"""
<div class="card {c}">
<div class="card-header">{i} {res['ticker']} <div class="score-badge">{puan}</div></div>
<div class="analysis-text"><b>{res['baslik']}</b><br>{res['analiz']}</div>
<div class="risk-row">
<span>R/R: <b style="color:#FFF;">{res['rr_orani']}</b></span>
<span>Kasa: <b style="color:#90caf9;">{res['kasa_yuzdesi']}</b></span>
</div>
<div class="strategy-grid">
<div><div class="stat-label">GİRİŞ</div><div class="stat-val">${res['giris']}</div></div>
<div><div class="stat-label">HEDEF</div><div class="stat-val">${res['hedef']}</div></div>
<div><div class="stat-label">STOP</div><div class="stat-val">${res['stop']}</div></div>
<div><div class="stat-label">VADE</div><div class="stat-val">{res['vade']}</div></div>
</div>
</div>
"""
    st.markdown(html_card, unsafe_allow_html=True)
    
    if res.get('news'):
        with st.expander(f"Haber Detayları ({res['ticker']})"):
            st.text("\n".join(res['news'][:3]))

# --- ARAYÜZ ---
st.title("🛡️ Sazlık: Şüpheci Mod")
st.markdown("---")

# 1. BÖLÜM: OTOMATİK
if st.button("TÜM FIRSATLARI TARA (LİDERLİK TABLOSU) 📊", type="primary"):
    news_dict = get_news_leads()
    
    if not news_dict: 
        st.warning("Veri çekilemedi. GitHub Actions'ı kontrol edin.")
    else:
        status = st.empty()
        bar = st.progress(0)
        tickers = list(news_dict.keys())
        results = []
        
        for i, ticker in enumerate(tickers):
            status.text(f"Analiz ediliyor: {ticker}...")
            bar.progress((i+1)/len(tickers))
            tech = get_technical_filter(ticker)
            if not tech: continue
            
            ai = score_opportunity(ticker, tech, news_dict[ticker])
            
            if ai:
                ai['ticker'] = ticker
                ai['news'] = news_dict[ticker]
                results.append(ai)
        
        status.empty(); bar.empty()
        results.sort(key=lambda x: x['puan'], reverse=True)
        
        if not results:
            st.info("Kriterlere uyan hisse çıkmadı.")
        else:
            for res in results:
                display_card(res)

st.markdown("---")

# 2. BÖLÜM: TEKLİ SEÇİM
with st.expander("🕵️ MANUEL ANALİZ", expanded=True):
    selected_ticker = st.selectbox("Hisse Seçiniz:", WATCHLIST)
    
    if st.button(f"{selected_ticker} ANALİZ ET 🔍"):
        with st.spinner(f"{selected_ticker} inceleniyor..."):
            all_news = get_news_leads()
            specific_news = all_news.get(selected_ticker, [])
            tech = get_technical_filter(selected_ticker)
            
            if not tech:
                st.error("Hisse verisi çekilemedi.")
            else:
                res = score_opportunity(selected_ticker, tech, specific_news)
                if res:
                    res['ticker'] = selected_ticker
                    res['news'] = specific_news
                    display_card(res)
