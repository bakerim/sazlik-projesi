import streamlit as st
import google.generativeai as genai
import feedparser
import json
import time
import yfinance as yf
import pandas as pd

# --- AYARLAR ---
st.set_page_config(page_title="Sazlık v6.0: Forensic Auditor", page_icon="🕵️‍♂️", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #000000; }
    .signal-card {
        padding: 15px; border-radius: 8px; margin-bottom: 15px;
        border-left: 6px solid; background-color: #111;
        font-family: 'Courier New', monospace;
    }
    .success { border-color: #00ff00; } 
    .warning { border-color: #ffa500; } 
    .rejected { border-color: #555; opacity: 0.6; } /* Elenenler için */
    h3 { color: #fff !important; margin: 0; }
    p { color: #ccc !important; }
    .badge {
        font-size: 0.75em; background: #222; padding: 3px 8px; 
        border-radius: 4px; border: 1px solid #444; margin-right: 5px; color: #fff;
    }
</style>
""", unsafe_allow_html=True)

# --- KAYNAKLAR ---
RSS_URLS = [
    "https://www.kap.org.tr/rss",
    "https://www.tcmb.gov.tr/wps/wcm/connect/tr/tcmb+tr/main+menu/duyurular/basin/rss",
    "https://news.google.com/rss/search?q=borsa+istanbul+şirket+haberleri&hl=tr&gl=TR&ceid=TR:tr",
    "https://finance.yahoo.com/news/rssindex",
    "https://www.federalreserve.gov/feeds/press_all.xml"
]

# --- 1. TICKER DOĞRULAMA (Anti-Halüsinasyon) ---
def validate_ticker(ticker_guess):
    if not ticker_guess or len(ticker_guess) > 10 or " " in ticker_guess: return None
    
    COMMON_FIXES = {
        "GALAT": "GSRAY.IS", "GSRAY": "GSRAY.IS", "THY": "THYAO.IS", "THYAO": "THYAO.IS",
        "GARAN": "GARAN.IS", "ASELS": "ASELS.IS", "SASA": "SASA.IS", "EREGL": "EREGL.IS",
        "KCHOL": "KCHOL.IS", "FBYD": "FBYD"
    }
    
    guess = COMMON_FIXES.get(ticker_guess, ticker_guess)
    
    # .IS Ekleme Mantığı
    if not guess.endswith(".IS") and not guess.isalpha(): pass 
    elif not guess.endswith(".IS") and len(guess) <= 5: guess += ".IS"

    try:
        stock = yf.Ticker(guess)
        # Hızlı kontrol için info yerine history kullan (daha hızlı ve güvenilir)
        hist = stock.history(period="1d")
        if not hist.empty:
            return guess
    except: pass
    return None

# --- 2. HACİM TEYİDİ (Volume Confirmation) ---
# "Haber gerçekse, büyük paralar da giriyor olmalı."
def check_volume_surge(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Son 5 günün verisini al
        hist = stock.history(period="5d")
        
        if len(hist) < 2: return False, 0, "Veri Yetersiz"
        
        current_vol = hist['Volume'].iloc[-1]
        avg_vol = hist['Volume'].mean()
        
        # Eğer hacim yoksa (0 ise) veya ortalamanın çok altındaysa haber YALANDIR/ETKİSİZDİR.
        # KURAL: Bugünkü hacim, ortalamanın en az %80'i kadar olmalı. 
        # (Tam patlama beklemiyoruz ama ölü taklidi de yapmamalı)
        if current_vol < (avg_vol * 0.8):
            return False, current_vol, "Hacim Çok Düşük (İlgi Yok)"
        
        return True, current_vol, "Hacim Onaylandı"
    except:
        return False, 0, "Hacim Verisi Yok"

# --- 3. FİYAT VE VOLATİLİTE KONTROLÜ ---
def check_price_reality(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        if len(hist) < 2: return None, None, None
        
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        change_pct = ((curr - prev) / prev) * 100
        
        return change_pct, curr, hist
    except: return None, None, None

# --- ÇÖP FİLTRESİ ---
def is_garbage(title):
    BAD = ["coin", "token", "kripto", "sponsor", "reklam", "iddia", "uzman", "tahmin", "analiz"]
    return any(b in title.lower() for b in BAD)

# --- PROMPT ---
SYSTEM_PROMPT = """
**GÖREV:** Borsa haberlerini analiz et. Sadece ŞİRKET KASASINA PARA GİREN somut olayları bul.

**KURALLAR:**
1. **SOMUT KANIT:** Sadece "İhale", "Bilanço", "Temettü", "Geri Alım" haberlerini kabul et. "Beklenti" haberlerini ÇÖPE AT.
2. **TICKER:** Hisse kodunu bilmiyorsan UNKNOWN yaz.
3. **ETKİ:** Bu haber hisseyi neden artırsın? 1 cümlelik finansal sebep yaz.

**OUTPUT (JSON):**
[{"Action": "AL", "Ticker": "THYAO", "Type": "İhale", "Confidence": 85, "Analysis": "..."}]
"""

# --- MOTOR ---
def analyze_market():
    if not st.session_state.get('api_key'):
        st.error("API Key giriniz.")
        return

    genai.configure(api_key=st.session_state.api_key)
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=SYSTEM_PROMPT)
    status = st.empty()
    
    # 1. Haber Toplama
    status.text("📡 Haberler toplanıyor...")
    headlines = []
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                if not is_garbage(entry.title):
                    headlines.append(f"- {entry.title}")
        except: pass

    if not headlines:
        st.error("Haber yok.")
        return

    # 2. AI Analizi
    status.text("🧠 İçerik Analizi Yapılıyor...")
    try:
        resp = model.generate_content("\n".join(headlines[:50]))
        signals = json.loads(resp.text.replace('```json','').replace('```','').strip())
        status.empty()
        
        if not signals:
            st.info("Temiz haber bulundu ama 'Somut Fırsat' (Para Girişi) tespit edilemedi.")
            return

        for s in signals:
            raw_ticker = s.get('Ticker', 'UNKNOWN')
            
            # --- AŞAMA 1: Ticker Doğrulama ---
            valid_ticker = validate_ticker(raw_ticker)
            if not valid_ticker: continue # Halüsinasyon silindi
            
            # --- AŞAMA 2: Hacim Dedektörü (YENİ) ---
            # Kimse almıyorsa, haber boştur.
            vol_ok, vol_val, vol_msg = check_volume_surge(valid_ticker)
            
            # --- AŞAMA 3: Fiyat/Gap Kontrolü ---
            pct, price, _ = check_price_reality(valid_ticker)
            
            # --- KARAR MEKANİZMASI ---
            final_decision = "ONAY"
            reject_reason = ""
            
            # Elekler:
            if not vol_ok:
                final_decision = "RED"
                reject_reason = f"⛔ {vol_msg} (Piyasa haberi takmıyor)"
            elif pct and pct > 2.0:
                final_decision = "RED"
                reject_reason = f"⛔ Fiyat Çok Şişmiş (%{pct:.2f} artış)"
            elif pct and pct < -2.0:
                final_decision = "RED"
                reject_reason = "⛔ Negatif Trend (Düşen Bıçak)"
            
            # EKRANA BASMA
            if final_decision == "ONAY":
                card_class = "success"
                icon = "💎"
                main_msg = f"GÜVENLİ GİRİŞ (Değişim: %{pct:.2f})"
            else:
                card_class = "rejected"
                icon = "🗑️"
                main_msg = f"FİLTRELENDİ: {reject_reason}"

            # Sadece ONAY alanları mı gösterelim yoksa elenenleri de mi?
            # Garantici adam neyin elendiğini de görmek ister ki sistemin çalıştığına güvensin.
            
            st.markdown(f"""
            <div class="signal-card {card_class}">
                <div style="display:flex; justify-content:space-between;">
                    <h3>{icon} {valid_ticker} <span style="font-size:0.6em; color:#888;">{s['Type']}</span></h3>
                    <span class="badge">{vol_msg}</span>
                </div>
                <div style="margin:10px 0; font-weight:bold; color:{'#4caf50' if final_decision=='ONAY' else '#ff5555'};">
                   {main_msg}
                </div>
                <p>{s['Analysis']}</p>
                <div style="font-size:0.8em; color:#666; margin-top:5px;">
                    Güven Puanı: %{s['Confidence']} | Fiyat: {price}
                </div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sistem Hatası: {e}")

# --- SIDEBAR ---
with st.sidebar:
    st.title("🕵️‍♂️ Forensic Mod")
    st.session_state.api_key = st.text_input("API Key", type="password")
    st.divider()
    st.info("""
    **BU MODUN FARKI:**
    Haber ne kadar iyi olursa olsun;
    1. **Hacim Düşükse** (Kimse almıyorsa)
    2. **Fiyat Şişmişse** (Gap varsa)
    
    Sistem sinyali **REDDEDER** ve neden reddettiğini yazar.
    """)

if st.button("DENETİMİ BAŞLAT (v6.0) 🚀"):
    analyze_market()
