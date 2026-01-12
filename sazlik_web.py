import streamlit as st
import pandas as pd
import yfinance as yf
from google import genai
import requests
import json
from datetime import datetime
import streamlit.components.v1 as components
import config


st.set_page_config(page_title="Sazlık Pro: Şüpheci Mod", page_icon="🛡️", layout="wide")

# --- API KONTROL ---
response = client.models.generate_content(
    model='gemini-2.0-flash-exp', # veya 'gemini-1.5-flash'
    contents="Senin promptun buraya"
)

# --- 500 HİSSELİK LİSTE ---
WATCHLIST = [
# --- TEKNOLOJİ & İLETİŞİM (En Büyük ve En Güvenilir) ---
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE", 
    "CRM", "CMCSA", "QCOM", "TXN", "AMGN", "INTC", "CSCO", "VZ", "T", "TMUS",
    "NFLX", "ORCL", "MU", "IBM", "PYPL", "INTU", "AMD", "FTNT", "ADI", "NOW",
    "LRCX", "MRVL", "CDNS", "SNPS", "DXCM", "KLAC", "ROST", "ANSS", "MSCI", "CHTR",
    
    # --- FİNANS & FİNANSAL HİZMETLER ---
    "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPY", "BLK", "SCHW",
    "C", "AXP", "CB", "MMC", "AON", "CME", "ICE", "PGR", "ALL", "MET",
    "AIG", "PNC", "USB", "BK", "COF", "DFS", "TRV", "MCO", "CBOE", "RJF",
    "GPN", "FIS", "ZION", "FITB", "STT", "NDAQ", "RF", "KEY", "CFG", "HBAN",
    
    # --- SAĞLIK & İLAÇ ---
    "JNJ", "LLY", "UNH", "ABBV", "MRK", "PFE", "DHR", "TMO", "MDT", "SYK",
    "AMGN", "GILD", "BIIB", "VRTX", "BMY", "ISRG", "ABT", "ZTS", "BDX", "BSX",
    "CI", "CVS", "HUM", "HCA", "ANTM", "LH", "COO", "ALGN", "HOLX", "DVA",
    "WAT", "RGEN", "IQV", "REGN", "EW", "TECH", "PKI", "DGX", "INCY", "CRL",
    
    # --- TEMEL TÜKETİM & DAYANIKLI TÜKETİM (İstikrar) ---
    "PG", "KO", "PEP", "WMT", "COST", "HD", "MCD", "NKE", "LOW", "TGT",
    "SBUX", "MDLZ", "CL", "PM", "MO", "KR", "DG", "ADBE", "EL", "KHC",
    "GIS", "K", "SYY", "APO", "DECK", "BBY", "WHR", "NWSA", "FOXA", "HAS",
    "MAT", "HOG", "GT", "TIF", "TPR", "TTC", "VFC", "HBI", "KSS", "ULTA",
    
    # --- ENERJİ & SANAYİ (Köklü Şirketler) ---
    "XOM", "CVX", "BRK.B", "LMT", "RTX", "BA", "HON", "MMM", "GE", "GD",
    "CAT", "DE", "EOG", "OXY", "SLB", "COP", "PSX", "MPC", "WMB", "KMI",
    "ETN", "AOS", "EMR", "PCAR", "ROK", "SWK", "TDY", "RSG", "WM", "CARR",
    "ITW", "GWW", "WAB", "IEX", "AAL", "DAL", "UAL", "LUV", "HA", "ALK",
    
    # --- EMLAK, KAMU HİZMETLERİ & DİĞER (Çeşitlilik) ---
    "DUK", "NEE", "SO", "EXC", "AEP", "SRE", "WEC", "D", "ED", "XEL",
    "VNQ", "SPG", "PLD", "EQIX", "AMT", "CCI", "HST", "O", "ARE", "PSA",
    "WY", "BXP", "REG", "VTR", "AVB", "ESR", "EPR", "KIM", "FRT", "APTS",
    "LUMN", "VIAC", "FOX", "DISCA", "ETSY", "EBAY", "ATVI", "EA", "TTWO", "ZG"

    # --- YARI İLETKEN & BULUT BİLİŞİM ---
    "ASML", "AMAT", "TSM", "MCHP", "TER", "U", "VEEV", "OKTA", "NET", "CRWD", 
    "DDOG", "ZS", "TEAM", "ADSK", "MSI", "FTV", "WDC", "ZBRA", "SWKS", "QDEL",

    # --- YENİLENEBİLİR ENERJİ & EV (Elektrikli Araçlar) ---
    "FSLY", "PLUG", "ENPH", "SEDG", "RUN", "SPWR", "BLDP", "FCEL", "BE", "SOL",
    "LI", "NIO", "XPEV", "RIVN", "LCID", "NKLA", "WKHS", "QS", "ARVL", "GOEV",

    # --- FİNANSAL TEKNOLOJİ (FinTech) & Dijital Ödeme ---
    "SQ", "COIN", "HOOD", "UPST", "AFRM", "SOFI", "MQ", "BILL", "TOST", "PAYA",
    "DWAC", "BRZE", "AVLR", "DOCU", "SABR", "TTEC", "TWLO", "RNG", "ZM", "COUP",
    
    # --- BİYOTEKNOLOJİ & SAĞLIK (Yüksek Büyüme) ---
    "MRNA", "PFE", "BIIB", "VRTX", "REGN", "GILD", "AMGN", "BMRN", "ALXN", "CTAS",
    "CORT", "EXEL", "IONS", "XBI", "LABU", "EDIT", "BEAM", "NTLA", "CRSP", "ALLK",

    # --- E-TİCARET & YENİ MEDYA ---
    "MELI", "ETSY", "ROKU", "PTON", "SPOT", "CHWY", "ZM", "DOCU", "DDOG", "FVRR",
    "PINS", "SNAP", "TWTR", "WIX", "SHOP", "SE", "BABA", "JD", "BIDU", "PDD",

    # --- ENDÜSTRİ & OTOMASYON (Orta Ölçekli ve Dinamik) ---
    "ROP", "TT", "Ametek", "FLR", "HUBB", "APH", "ECL", "SHW", "PPG", "FMC",
    "MOS", "CF", "NUE", "STLD", "ALK", "AAL", "DAL", "LUV", "UAL", "SAVE",
    "CAR", "RCL", "CCL", "NCLH", "MGM", "WYNN", "LVS", "PENN", "DKNG", "BYND",

    # --- ÇEŞİTLİ DİNAMİK BÜYÜME (Mid-Cap/IPO) ---
    "RBLX", "UBER", "LYFT", "ABNB", "DOX", "GPN", "FLT", "PRU", "MET", "L",
    "VLO", "PSX", "MPC", "DVN", "APA", "MRO", "EOG", "OXY", "SLB", "HAL",
    "BKR", "FTI", "NOV", "TDW", "PAGP", "ENLC", "PAA", "WES", "WMB", "KMI",
    "ETN", "AOS", "EMR", "PCAR", "ROK", "SWK", "TDY", "RSG", "WM", "CARR"
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
        response = requests.get(url, timeout=5)
        if response.status_code != 200: return {}
        data = response.json()
        leads = {}
        for item in data:
            ticker = item.get('ticker')
            if ticker:
                if ticker not in leads: leads[ticker] = []
                leads[ticker].append(f"- {item['content']}")
        return leads
    except: return {}

def fetch_live_news_fallback(ticker):
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if not news: return []
        return [f"- {n['title']}" for n in news[:3]]
    except: return []

def score_opportunity(ticker, tech_data, news_list):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    news_text = "\n".join(news_list[:3]) if news_list else "Haber bulunamadı."
    
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

# --- KART GÖSTERİMİ (TEK SATIR TEKNİĞİ - ASLA BOZULMAZ) ---
def display_card(res):
    puan = res['puan']
    
    if puan >= 85: c, i = "tier-s", "💎"
    elif puan >= 75: c, i = "tier-a", "🔥"
    elif puan >= 60: c, i = "tier-b", "⚠️"
    else: c, i = "tier-fail", "⛔"

    # AŞAĞIDAKİ SATIR BİLEREK TEK PARÇA HALİNDE YAZILDI. LÜTFEN BÖLMEYİN.
    # Bu, Streamlit'in HTML'i kod sanmasını %100 engeller.
    html_card = f"""<div class="card {c}"><div class="card-header">{i} {res['ticker']} <div class="score-badge">{puan}</div></div><div class="analysis-text"><b>{res['baslik']}</b><br>{res['analiz']}</div><div class="risk-row"><span>R/R: <b style="color:#FFF;">{res['rr_orani']}</b></span><span>Kasa: <b style="color:#90caf9;">{res['kasa_yuzdesi']}</b></span></div><div class="strategy-grid"><div><div class="stat-label">GİRİŞ</div><div class="stat-val">${res['giris']}</div></div><div><div class="stat-label">HEDEF</div><div class="stat-val">${res['hedef']}</div></div><div><div class="stat-label">STOP</div><div class="stat-val">${res['stop']}</div></div><div><div class="stat-label">VADE</div><div class="stat-val">{res['vade']}</div></div></div></div>"""
    
    st.markdown(html_card, unsafe_allow_html=True)
    
    if res.get('news'):
        with st.expander(f"Haber Detayları ({res['ticker']})"):
            st.text("\n".join(res['news'][:3]))

# --- ARAYÜZ ---
st.title("🛡️ Sazlık: Garantici Mod")
st.markdown("---")

# 1. BÖLÜM: OTOMATİK
if st.button("Analize Başla", type="primary"):
    news_dict = get_news_leads()
    
    if not news_dict: 
        st.warning("Bot henüz veri toplamamış veya erişilemiyor. (Manuel analiz çalışır)")
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
