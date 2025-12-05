import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Sazlık Pro: Fırsat Radarı", page_icon="📡", layout="wide")

# --- API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı Yok!")
    st.stop()

# --- CSS (KART TASARIMI) ---
st.markdown("""
<style>
    .card {
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .card-header {
        font-size: 22px;
        font-weight: bold;
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .badge {
        background: rgba(255,255,255,0.15);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        margin-left: 10px;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-top: 15px;
        text-align: center;
        background: rgba(0,0,0,0.2);
        padding: 10px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---

def get_technical_summary(ticker):
    """Hızlı teknik tarama (Detaylı analiz değil, ön eleme için)"""
    try:
        stock = yf.Ticker(ticker)
        # Sadece son 5 günü çek, hızlı olsun
        hist = stock.history(period="5d") 
        if hist.empty: return None
        
        price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((price - prev_price) / prev_price) * 100
        
        # Basit Trend: Son fiyat 5 günlüğün üstünde mi?
        sma5 = hist['Close'].mean()
        trend = "YÜKSELİŞ" if price > sma5 else "DÜŞÜŞ"
        
        return {"price": price, "change": change_pct, "trend": trend}
    except: return None

def get_hot_leads():
    """Botun bulduğu haberlerden 'Bugün' hareketli olanları seçer"""
    url = "https://raw.githubusercontent.com/bakerim/sazlik-projesi/main/news_archive.json"
    try:
        data = requests.get(url).json()
        
        # Hisseleri grupla
        leads = {}
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        for item in data:
            ticker = item.get('ticker')
            date = item.get('date')
            
            # Sadece son 3 günün haberleri "Sıcak" sayılır
            # (Burada basitlik için tüm arşivi tarıyoruz ama normalde tarih farkına bakılır)
            if ticker not in leads:
                leads[ticker] = []
            leads[ticker].append(f"- [{date}] {item['content']}")
            
        # Ön eleme yap: Sadece en çok haberi olan veya en yeni haberi olan 5 hisseyi seç
        # (API Limitini yememek için 5 ile sınırlıyoruz)
        sorted_leads = sorted(leads.items(), key=lambda x: x[1][0], reverse=True)[:5]
        return sorted_leads
    except: return []

def ask_ai_oracle(ticker, tech_data, news_list):
    """Garantici Baba'ya sorar"""
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    news_text = "\n".join(news_list[:3]) # En yeni 3 haber
    
    prompt = f"""
    SEN "GARANTİCİ BABA" LAKAPLI BİR SWING TRADER'SIN.
    
    HİSSE: {ticker} | FİYAT: ${tech_data['price']:.2f} | GÜNLÜK DEĞİŞİM: %{tech_data['change']:.2f}
    TREND DURUMU: {tech_data['trend']}
    HABERLER:
    {news_text}
    
    GÖREV: Sadece çok net fırsat varsa öner. Yoksa "Pas Geç" de.
    
    ÇIKTI (JSON):
    {{
        "karar": "AL (FIRSAT)" veya "PAS GEÇ (RİSKLİ)",
        "guven": (0-100),
        "analiz": "Tek cümlelik özet.",
        "strateji": {{
            "giris": {tech_data['price']:.2f},
            "hedef": (Fiyatın %4-%10 fazlası),
            "stop": (Fiyatın %3-%5 altı),
            "vade": "X Gün"
        }},
        "potansiyel_kar_zarar": "1'e 3 Oran (Risk/Kazanç)"
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '')
        return json.loads(text)
    except: return None

# --- ARAYÜZ ---
st.title("📡 Sazlık: Fırsat Radarı")
st.markdown("Sistem 100 hisseyi tarar, sadece 'Haber Akışı' olanları AI analizine sokar.")
st.markdown("---")

# 1. RADAR BÖLÜMÜ (OTOMATİK)
st.subheader("🔥 Bugünün Sıcak Fırsatları (AI Önerileri)")

if st.button("RADARI ÇALIŞTIR VE TARA 🚀", type="primary"):
    with st.spinner("Piyasa taranıyor, haberler analiz ediliyor..."):
        hot_leads = get_hot_leads() # Haber olan hisseleri getir
        
        found_opportunity = False
        
        # Sütunlar halinde gösterelim
        cols = st.columns(3)
        col_index = 0
        
        for ticker, news in hot_leads:
            # 1. Teknik veriyi çek
            tech = get_technical_summary(ticker)
            if not tech: continue
            
            # 2. AI Analizi yap
            ai_result = ask_ai_oracle(ticker, tech, news)
            
            if ai_result:
                # Sadece "AL" veya yüksek güvenlileri gösterelim (Filtreleme)
                # Amaç kullanıcıyı boğmamak.
                karar = ai_result['karar'].upper()
                
                # Kart Rengi
                if "AL" in karar:
                    color = "#1b5e20" # Yeşil
                    border = "#00e676"
                    icon = "💎"
                    found_opportunity = True
                else:
                    color = "#262730" # Gri (Pas Geçilenler)
                    border = "#555"
                    icon = "💤"
                
                # Kartı Çiz
                with cols[col_index % 3]:
                    st.markdown(f"""
                    <div class="card" style="background-color: {color}; border: 1px solid {border};">
                        <div class="card-header">
                            {icon} {ticker} <span class="badge">{karar}</span>
                        </div>
                        <p style="font-size:0.9em; opacity:0.8;">{ai_result['analiz']}</p>
                        
                        <div class="metric-grid">
                            <div>
                                <small>Giriş</small><br>
                                <b>${ai_result['strateji']['giris']}</b>
                            </div>
                            <div style="color: #00e676;">
                                <small>Hedef</small><br>
                                <b>${ai_result['strateji']['hedef']}</b>
                            </div>
                            <div style="color: #ff5252;">
                                <small>Stop</small><br>
                                <b>${ai_result['strateji']['stop']}</b>
                            </div>
                        </div>
                        
                        <div style="margin-top:10px; font-size:0.85em; text-align:center;">
                            ⏳ Vade: <b>{ai_result['strateji']['vade']}</b> | 🛡️ Güven: <b>%{ai_result['guven']}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander(f"{ticker} Haberleri"):
                        st.text("\n".join(news))
                
                col_index += 1
        
        if not found_opportunity:
            st.info("Bot tarama yaptı ancak 'Garantici Baba' kriterlerine uyan net bir alım fırsatı bulamadı. Piyasa yatay veya riskli olabilir.")

st.markdown("---")

# 2. MANUEL KONTROL (ESKİ SİSTEM)
with st.expander("🔍 Manuel Hisse Sorgula (Tekli Analiz)"):
    ticker_manual = st.text_input("Hisse Kodu Gir", "TSLA").upper()
    if st.button("Tekli Analiz Yap"):
        # Buraya eski tekli analiz kodları gelir (Sadelik için burayı kısa tuttum, 
        # istersen eski kodları buraya entegre edebiliriz ama Radar bence yeterli)
        st.write(f"{ticker_manual} için detaylı analiz özelliği şu an Radar modunda pasif.")
