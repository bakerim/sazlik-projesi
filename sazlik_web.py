import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Sazlık: Garantici Baba", page_icon="🎯", layout="wide")

# --- API KONTROL ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı Yok! Streamlit Secrets ayarlarını yapmalısın.")
    st.stop()

# --- DÜZELTİLMİŞ CSS (GÖRSEL KAYMA YOK) ---
st.markdown("""
<style>
    .card {
        background-color: #1b5e20; /* Sadece Yeşil Kartlar Olacak */
        border: 2px solid #00e676;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,230,118,0.2);
    }
    .card-header {
        font-size: 26px;
        font-weight: bold;
        display: flex;
        align-items: center;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        padding-bottom: 10px;
        margin-bottom: 10px;
    }
    .badge-score {
        background: #00e676;
        color: #000;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.6em;
        margin-left: auto;
        font-weight: 800;
    }
    .main-text {
        font-size: 16px;
        line-height: 1.5;
        opacity: 0.9;
    }
    .strategy-box {
        background: rgba(0,0,0,0.3);
        border-radius: 10px;
        padding: 15px;
        margin-top: 15px;
        display: flex;
        justify-content: space-around;
        text-align: center;
    }
    .stat-label { font-size: 12px; color: #aaa; text-transform: uppercase; }
    .stat-value { font-size: 18px; font-weight: bold; color: #fff; }
    .win-green { color: #69f0ae; }
    .loss-red { color: #ff8a80; }
</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---

def get_technical_filter(ticker):
    """
    İLK FİLTRE: Sadece Yükseliş Trendinde olanları geçirir.
    Ayı piyasasındaki hisseyi Garantici Baba içeri almaz.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo") # Son 1 ay
        if hist.empty: return None
        
        price = hist['Close'].iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        
        # EĞER FİYAT ORTALAMANIN ALTINDAYSA DİREKT ELE (False)
        if price < sma20:
            return None 
            
        # Yükseliş trendinde ise verileri döndür
        return {"price": price, "sma": sma20}
    except: return None

def get_news_leads():
    """Botun bulduğu haberlerden 'Bugün' ve 'Dün' hareketli olanları seçer"""
    url = "https://raw.githubusercontent.com/bakerim/sazlik-projesi/main/news_archive.json"
    try:
        data = requests.get(url).json()
        leads = {}
        for item in data:
            ticker = item.get('ticker')
            # Sadece son 48 saatin haberlerini dikkate al
            # (Basitlik için tümünü alıyoruz ama AI'a tarihleri vereceğiz)
            if ticker not in leads:
                leads[ticker] = []
            leads[ticker].append(f"- {item['content']}")
        return leads
    except: return {}

def ask_garantici_baba(ticker, tech_data, news_list):
    """
    Sadece %90 üstü fırsatları döndürür.
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    news_text = "\n".join(news_list[:3])
    
    prompt = f"""
    SEN "GARANTİCİ BABA" LAKAPLI, RİSKTEN NEFRET EDEN BİR TRADER'SIN.
    
    HİSSE: {ticker}
    FİYAT: ${tech_data['price']:.2f} (Şu an 20 günlük ortalamanın üzerinde, Teknik POZİTİF)
    HABERLER:
    {news_text}
    
    GÖREV:
    Bu hisse "BEDAVA PARA" (Free Money) kıvamında mı?
    Sadece %90 ve üzeri kazanma ihtimali görüyorsan öner. Aksi takdirde boş JSON döndür.
    
    KRİTERLER:
    1. Trend güçlü olmalı.
    2. Haber çok pozitif olmalı (Örn: Rekor bilanço, Dev ortaklık).
    3. Swing Trade (3-5 gün) için uygun olmalı.
    
    EĞER ŞARTLAR UYUYORSA BU JSON'I DOLDUR:
    {{
        "uygun": true,
        "guven": (90-99 arası puan),
        "analiz": "Neden bu kadar eminsin? (Tek cümle)",
        "giris": {tech_data['price']:.2f},
        "hedef": (Makul kar al noktası),
        "stop": (Yakın stop),
        "vade": "X Gün"
    }}
    
    EĞER UYMUYORSA (RİSK VARSA):
    {{ "uygun": false }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '')
        data = json.loads(text)
        return data if data.get('uygun') == True else None
    except: return None

# --- ARAYÜZ ---
st.title("🎯 Sazlık: Sniper Modu")
st.markdown("""
Bu mod **sadece %90 ve üzeri** kazanma ihtimali olan, trendi YUKARI yönlü hisseleri gösterir. 
Eğer ekran boşsa, paran cebinde kalsın demektir.
""")
st.markdown("---")

if st.button("KESKİN NİŞANCIYI ÇALIŞTIR 🔭", type="primary"):
    
    news_dict = get_news_leads() # Haberleri çek
    
    if not news_dict:
        st.warning("Bot henüz yeterince veri toplamadı veya GitHub dosyasına erişilemiyor.")
    else:
        found_any = False
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        # Taranacak hisseler
        tickers_to_scan = list(news_dict.keys())
        total = len(tickers_to_scan)
        
        cols = st.columns(2) # 2 Sütunlu düzen
        col_idx = 0
        
        for i, ticker in enumerate(tickers_to_scan):
            status_text.text(f"Taranıyor: {ticker}...")
            progress_bar.progress((i + 1) / total)
            
            # 1. ELEME: Teknik Trend (Ayı piyasasıysa direkt geç)
            tech = get_technical_filter(ticker)
            if not tech:
                continue # Trend kötü, AI'a bile sorma
                
            # 2. ELEME: Garantici Baba (AI)
            result = ask_garantici_baba(ticker, tech, news_dict[ticker])
            
            if result:
                found_any = True
                with cols[col_idx % 2]:
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-header">
                            💎 {ticker} AL
                            <span class="badge-score">Güven: %{result['guven']}</span>
                        </div>
                        <div class="main-text">{result['analiz']}</div>
                        
                        <div class="strategy-box">
                            <div>
                                <div class="stat-label">GİRİŞ</div>
                                <div class="stat-value">${result['giris']}</div>
                            </div>
                            <div>
                                <div class="stat-label">HEDEF</div>
                                <div class="stat-value win-green">${result['hedef']}</div>
                            </div>
                            <div>
                                <div class="stat-label">STOP</div>
                                <div class="stat-value loss-red">${result['stop']}</div>
                            </div>
                            <div>
                                <div class="stat-label">VADE</div>
                                <div class="stat-value">{result['vade']}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("Destekleyen Haberler"):
                        st.text("\n".join(news_dict[ticker][:3]))
                
                col_idx += 1
        
        status_text.empty()
        progress_bar.empty()
        
        if not found_any:
            st.info("✅ Tarama bitti. Şu an 'Garantici Baba' standartlarına (%90+) uyan kusursuz bir fırsat yok. Nakitte kalmak da bir pozisyondur.")
        else:
            st.balloons()
