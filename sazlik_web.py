import streamlit as st
import google.generativeai as genai
import feedparser
import json
import time
import yfinance as yf

# --- 1. SAYFA VE GÖRÜNÜM AYARLARI ---
st.set_page_config(page_title="Sazlık v4.2: Profit & Shield", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .signal-card {
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border-left: 6px solid;
        background-color: #161b22;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .vip-source { 
        background-color: #1f6feb; color: white; 
        padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;
    }
    .success { border-color: #2ea043; } /* Yeşil */
    .warning { border-color: #db6d28; } /* Turuncu */
    .danger { border-color: #da3633; }  /* Kırmızı */
    h3 { color: #f0f6fc !important; margin-top: 0; }
    p { color: #c9d1d9 !important; font-size: 1.05em; }
    .metric-box {
        background: #0d1117; border: 1px solid #30363d;
        padding: 10px; border-radius: 6px; margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. HABER KAYNAKLARI (EN GENİŞ AĞ) ---
RSS_URLS = [
    # VIP KAYNAKLAR (Güven +10)
    "https://www.tcmb.gov.tr/wps/wcm/connect/tr/tcmb+tr/main+menu/duyurular/basin/rss",
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "https://www.kap.org.tr/rss",
    
    # GLOBAL VE YEREL İSTİHBARAT
    "https://news.google.com/rss/search?q=borsa+istanbul+kap+bildirimleri&hl=tr&gl=TR&ceid=TR:tr",
    "https://news.google.com/rss/search?q=stock+market+earnings+reports&hl=en-US&gl=US&ceid=US:en",
    "https://finance.yahoo.com/news/rssindex",
    "https://www.cnbce.com/rss/piyasalar",
    "https://tr.investing.com/rss/news_25.rss"
]

# --- 3. FİLTRELER (ÇÖP VE SİYASET ELEĞİ) ---
def is_garbage_news(title):
    BLACKLIST = [
        "coin", "token", "kripto", "bitcoin", "ethereum", "shiba", "meme",
        "sponsorlu", "reklam", "ilandır", "tanıtım", 
        "şok iddia", "korkutan tahmin", "uzmanlar uyardı", "analist görüşü"
    ]
    title_lower = title.lower()
    return any(bad_word in title_lower for bad_word in BLACKLIST)

def hybrid_political_filter(news_text, news_source, is_bist_stock=False):
    text_lower = news_text.lower()
    source_lower = news_source.lower()
    
    # VIP Kaynaklar
    VIP_SOURCES = ["tcmb", "merkez bankası", "fed", "federal reserve", "kap", "reuters", "bloomberg"]
    # Siyasi Tetikleyiciler
    POLITICAL_TRIGGERS = ["erken seçim", "kabine", "istifa", "yaptırım", "savaş", "askeri", "ohal"]

    has_risk = any(word in text_lower for word in POLITICAL_TRIGGERS)
    is_vip = any(ts in source_lower for ts in VIP_SOURCES)

    if has_risk and is_bist_stock:
        if is_vip:
            return False, f"⛔ <b>KIRMIZI ALARM:</b> VIP Kaynak ({news_source}) siyasi risk bildirdi. BIST İşlemleri Durduruldu."
        else:
            return False, f"🗑️ <b>Dedikodu:</b> '{news_source}' siyasi risk üretti, güvenilir değil. Yoksayıldı."
            
    # Eğer haber VIP kaynaktan geliyorsa bunu belirtelim
    source_tag = "⭐ VIP KAYNAK" if is_vip else "Standart Kaynak"
    
    return True, source_tag

# --- 4. FİYAT VE TREND KONTROLÜ (GAP FIX) ---
def get_price_data(ticker):
    found_ticker = ticker
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        # BIST kontrolü
        if hist.empty:
            found_ticker = f"{ticker}.IS"
            stock = yf.Ticker(found_ticker)
            hist = stock.history(period="5d")

        if not hist.empty and len(hist) >= 2:
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] # Dünkü kapanış
            
            change_percent = ((current_price - prev_close) / prev_close) * 100
            return change_percent, current_price, found_ticker
        return None, None, None
    except:
        return None, None, None

# --- 5. ARAYÜZ ---
with st.sidebar:
    st.title("🎛️ Kontrol Kulesi")
    st.caption("Sazlık v4.2 (Profit & Shield)")
    api_key = st.text_input("Google Gemini API Key", type="password")
    
    st.divider()
    st.success("✅ **Strateji:** Çıkarcı & Garantici")
    st.info("🛡️ **Aktif Korumalar:**\n- Çöp Haber Eleği\n- Siyaset Dedektörü\n- Gap/Tuzak Kontrolü")

st.title("🏛️ Sazlık: Akıllı Yatırım İstihbaratı")
st.markdown("""
> *"Borsada fırsatlar bitmez ama sermaye biter. Önce paranı koru, sonra kar et."*
""")

# --- 6. PROMPT (ÇIKARCI VE GARANTİCİ BEYİN) ---
SYSTEM_PROMPT = """
**ROLE:**
Sen "Sazlık Projesi"nin Baş Stratejistisin. Kimliğin: Acımasızca seçici, çıkarcı (kar odaklı) ve garantici bir Swing Trader.
Kullanıcın (Mert), bir aile babasıdır. Kumar oynamaz, sadece "Net Fırsat" (Free Lunch) arar.

**GÖREV:**
Haberleri analiz et ve sadece PARANIN KOKUSUNU aldığın somut fırsatları getir.

**ANALİZ KURALLARI (ÇIKARCI STRATEJİ):**
1. **SOMUT KATALİZÖR ARA:** "Bilanço Karı", "Temettü", "Yeni İş Anlaşması", "Geri Alım (Buyback)". Bunlar para demektir.
2. **YUMUŞAK HABERLERİ ELE:** "Hedef fiyat revizesi", "Analist tahmini", "Sektör raporu" -> BUNLAR PARA KAZANDIRMAZ. YOKSAY.
3. **VIP KAYNAK AYRICALIĞI:** Haber FED, TCMB veya KAP kaynaklıysa ciddiye al.
4. **VADE:** 3-7 Günlük vur-kaç (Swing) fırsatı mı?

**OUTPUT FORMAT (JSON List):**
Fırsat yoksa [] döndür. Varsa:
[
  {
    "Action": "AL (LONG)",
    "Ticker": "HİSSE KODU (Örn: THYAO)",
    "Confidence": 85,
    "Risk_Level": "Düşük",
    "Analysis": "Kısa, net ve çıkarcı analiz cümlesi...",
    "Entry_Plan": "Kasanın %20'si. Agresif/Temkinli giriş.",
    "Stop_Loss": "%X",
    "Target": "%Y"
  }
]
"""

# --- 7. ANALİZ MOTORU ---
def analyze_market():
    if not api_key:
        st.error("⚠️ Önce API Anahtarını gir.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=SYSTEM_PROMPT)

    status_text = st.empty()
    bar = st.progress(0)
    
    # A. Haber Toplama ve Ön Eleme
    status_text.text("📡 Ağlar taranıyor, çöpler ayıklanıyor...")
    clean_headlines = []
    
    for i, url in enumerate(RSS_URLS):
        try:
            feed = feedparser.parse(url)
            src_name = feed.feed.get('title', 'Web Kaynağı')
            
            for entry in feed.entries[:5]: # Son 5 haber
                if not is_garbage_news(entry.title):
                    clean_headlines.append(f"- {entry.title} || Kaynak: {src_name}")
        except:
            continue
        bar.progress((i + 1) / len(RSS_URLS))

    if not clean_headlines:
        st.error("Filtrelerden geçen temiz haber bulunamadı.")
        return

    # B. AI Analizi
    status_text.text(f"🧠 {len(clean_headlines)} adet 'Temiz Veri' stratejiste sunuluyor...")
    
    # Token tasarrufu için son 35 başlık
    prompt_content = "\n".join(clean_headlines[:35])
    
    try:
        response = model.generate_content(f"Haberler:\n{prompt_content}")
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        
        try:
            signals = json.loads(clean_json)
        except:
            signals = []
        
        status_text.empty()
        bar.progress(100)
        time.sleep(0.5)
        bar.empty()
        
        # C. Sonuç Ekranı
        if not signals:
            st.info("🤷‍♂️ **Stratejist Raporu:** Şu an masada 'Bedava Öğle Yemeği' (Net Fırsat) yok. Nakitte kalmak en iyisi.")
            with st.expander("İncelenen Haberler"):
                for h in clean_headlines: st.write(h)
        else:
            for s in signals:
                ticker = s.get('Ticker', 'UNKNOWN')
                
                # Siyaset Kontrolü (Post-Filter)
                is_bist = ("IS" in ticker) or (len(ticker) == 5 and ticker.isupper())
                pass_pol, source_label = hybrid_political_filter(s['Analysis'], "Genel", is_bist)
                
                if not pass_pol:
                    st.error(source_label)
                    continue

                # Fiyat Kontrolü
                pct_change, price, valid_ticker = get_price_data(ticker)
                
                # Karar Mantığı
                is_late = False
                price_msg = ""
                box_color = "success" if s['Confidence'] > 85 else "warning"
                
                if pct_change is not None:
                    # 1. HATA: Tren Kaçtı mı? (Gap > %4)
                    if pct_change > 4.0:
                        is_late = True
                        price_msg = f"⚠️ <b>GEÇ KALDIN:</b> Bugün zaten <b>%{pct_change:.2f}</b> artmış. Düzeltme bekle."
                        box_color = "warning"
                    # 2. HATA: Düşen Bıçak mı? (Düşüş > %-3)
                    elif pct_change < -3.0:
                        is_late = True # Garantici adam düşen bıçağı tutmaz
                        price_msg = f"🛑 <b>DÜŞEN BIÇAK:</b> Haber iyi ama hisse <b>%{pct_change:.2f}</b> düşüşte. Trend negatif."
                        box_color = "danger"
                    else:
                        price_msg = f"✅ <b>Fiyat Uygun:</b> Değişim %{pct_change:.2f}. Giriş yapılabilir."
                else:
                    price_msg = f"ℹ️ Fiyat verisi alınamadı ({ticker}). Manuel bak."

                # Kart Başlığı
                title_prefix = "🚨 RİSKLİ:" if is_late else "💎 FIRSAT:"
                
                html = f"""
                <div class="signal-card {box_color}">
                    <div style="display:flex; justify-content:space-between;">
                        <h3>{title_prefix} {ticker} ({s['Action']})</h3>
                        <span class="vip-source">{source_label}</span>
                    </div>
                    <div class="metric-box">
                        {price_msg}
                    </div>
                    <p><b>Güven:</b> %{s['Confidence']} | <b>Risk:</b> {s['Risk_Level']}</p>
                    <p>📝 <b>Analiz:</b> {s['Analysis']}</p>
                    <hr style="border-color: #30363d;">
                    <p>💰 <b>Kasa:</b> {s['Entry_Plan']}</p>
                    <div style="display:flex; gap: 15px;">
                        <span style="color:#da3633;">🛑 Stop: {s['Stop_Loss']}</span>
                        <span style="color:#2ea043;">🎯 Hedef: {s['Target']}</span>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")

# --- 8. BAŞLAT BUTONU ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("ANALİZİ BAŞLAT (v4.2) 🚀", use_container_width=True):
        analyze_market()
