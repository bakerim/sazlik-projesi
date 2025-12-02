import streamlit as st
import google.generativeai as genai
import feedparser
import json
import time
import yfinance as yf

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık: SwingSniper", page_icon="🎯", layout="wide")

# --- 2. CSS TASARIM ---
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .signal-card {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid;
        background-color: #1c1c1c;
    }
    .success { border-color: #00ff00; } 
    .warning { border-color: #ffaa00; } 
    .danger { border-color: #ff0000; }  
    h3 { color: #ffffff !important; }
    p { color: #e0e0e0 !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. AKILLI FİYAT FONKSİYONU (GAP VE TİCKER DÜZELTME) ---
def get_price_data(ticker):
    """
    1. Önce verilen Ticker'ı dener.
    2. Olmazsa sonuna .IS ekleyip dener (BIST hisseleri için).
    3. Dünkü kapanışa göre % değişimi hesaplar (Gap-Up tuzağına düşmemek için).
    """
    found_ticker = ticker 
    
    try:
        # 1. Deneme: Saf Ticker
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        # 2. Deneme: Veri yoksa BIST olabilir (.IS ekle)
        if hist.empty:
            found_ticker = f"{ticker}.IS"
            stock = yf.Ticker(found_ticker)
            hist = stock.history(period="5d")

        # Veri kontrolü ve Hesaplama
        if not hist.empty and len(hist) >= 2:
            current_price = hist['Close'].iloc[-1]   # Anlık Fiyat
            prev_close = hist['Close'].iloc[-2]      # Dünkü Kapanış (Referans)
            
            # Gerçek Yüzdelik Değişim (Dünden Bugüne)
            change_percent = ((current_price - prev_close) / prev_close) * 100
            return change_percent, current_price, found_ticker
        else:
            return None, None, None
            
    except Exception as e:
        return None, None, None

# --- 4. KENAR ÇUBUĞU ---
with st.sidebar:
    st.title("🎛️ Kontrol Paneli")
    st.write("Sazlık Projesi - Web v3.3 Final")
    api_key = st.text_input("Google Gemini API Key", type="password")
    st.divider()
    st.info("💡 **Garantici Mod Açık:**\nSistem; global riskleri, ticker hatalarını ve anlık fiyat şişkinliğini (Gap) kontrol eder.")

# --- 5. ANA EKRAN ---
st.title("🎯 SwingSniper: Sazlık Projesi")
st.markdown("**Durum:** `Sistem Aktif` | **Mod:** `Defansif / Aile Babası` | **Versiyon:** `v3.3 (Gap Fix)`")

# --- 6. PROMPT (YAPAY ZEKA TALİMATI - DÜZELTİLDİ) ---
SYSTEM_PROMPT = """
**ROLE:**
Sen "Sazlık Projesi"nin Baş Stratejistisin. Kimliğin: Aşırı şüpheci, garantici ve defansif bir Swing Trader. 
Kullanıcın (Mert), sermayesi kısıtlı bir aile babasıdır. Kaybetme lüksü yoktur.

**GÖREV:**
Sana verilen finansal haberleri analiz et. Aşağıdaki "GÜVENLİK PROTOKOLÜ"nden geçmeyen her şeyi ELE.

**GÜVENLİK PROTOKOLÜ (4 KATMANLI FİLTRE):**
1. **GLOBAL İKLİM KONTROLÜ:** Piyasada genel bir çöküş, savaş riski veya teknoloji balonu patlaması (örn: Nvidia çöküşü) var mı? Varsa SİNYAL ÜRETME.
2. **HABER KALİTESİ:** Haber dedikodu mu? Elon Musk tweeti mi? Eğer öyleyse YOKSAY. Sadece şirketin kasasını etkileyecek gerçek haberlere bak.
3. **VADE KONTROLÜ:** Fırsat 3-5 gün sürecek mi? Anlık "pump-dump" ise YOKSAY.
4. **KASA YÖNETİMİ:** Asla "Tüm paranı bas" deme. Güvene göre kasanın %10'u veya en fazla %20'si ile işlem öner.

**OUTPUT FORMAT (JSON Listesi Olarak):**
Eğer uygun fırsat yoksa boş liste [] döndür. Varsa şu formatta döndür:
[
  {
    "Action": "AL (LONG)",
    "Ticker": "HİSSE KODU (Örn: THYAO)",
    "Confidence": 92,
    "Risk_Level": "Düşük/Orta",
    "Entry_Plan": "Kasanın %20'si ile gir. 3-5 Gün bekle.",
    "Reason": "Haberin detayı ve neden güvenli olduğu...",
    "Stop_Loss": "%2 Zarar Kes",
    "Target": "%5 Kar Al"
  }
]
"""

# --- 7. RSS KAYNAKLARI ---
RSS_URLS = [
    "https://tr.investing.com/rss/news_25.rss", # Borsa İstanbul Haberleri
    "https://tr.investing.com/rss/news_1.rss",  # Forex/Emtia Haberleri
    "https://finance.yahoo.com/news/rssindex"   # Global Kontrol
]

# --- 8. ANALİZ MOTORU ---
def analyze_market():
    if not api_key:
        st.error("⚠️ Lütfen önce sol menüden API Anahtarını gir.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=SYSTEM_PROMPT)

    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # --- A. Haberleri Topla ---
    status_text.text("📡 Haberler taranıyor...")
    all_headlines = []
    
    for i, url in enumerate(RSS_URLS):
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: 
                all_headlines.append(f"- {entry.title} (Kaynak: {feed.feed.get('title', 'Web')})")
        except:
            pass
        progress_bar.progress((i + 1) / len(RSS_URLS))

    if not all_headlines:
        st.error("Haber kaynağına ulaşılamadı. İnternet bağlantını kontrol et.")
        return

    # --- B. Yapay Zeka Analizi ---
    status_text.text(f"🧠 {len(all_headlines)} adet veri analiz ediliyor...")
    prompt = "Şu anki piyasa haberleri aşağıdadır. Protokole göre analiz et:\n" + "\n".join(all_headlines)
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        
        try:
            signals = json.loads(clean_text)
        except json.JSONDecodeError:
            st.error("Yapay zeka format hatası yaptı. Tekrar dene.")
            signals = []
        
        status_text.text("✅ Analiz bitti! Sonuçlar işleniyor...")
        progress_bar.progress(100)
        time.sleep(1)
        status_text.empty() 
        
        # --- C. Sonuçları Ekrana Bas ---
        if not signals:
            st.info("🤷‍♂️ **Şu an 'Garantici Protokol'e uyan FIRSAT YOK.** Piyasa riskli veya haberler yetersiz.")
            with st.expander("Taranan Haber Başlıklarını Gör"):
                for h in all_headlines:
                    st.write(h)
        else:
            for s in signals:
                ticker_raw = s.get('Ticker', 'UNKNOWN')
                
                # --- D. FİYAT KONTROLÜ (Düzeltilmiş) ---
                real_change, real_price, valid_ticker = get_price_data(ticker_raw)
                
                is_late = False
                price_warning = ""
                color_class = "success" if s['Confidence'] > 85 else "warning"

                # 1. Durum: Fiyat Verisi Başarıyla Çekildi
                if real_change is not None:
                    # KURAL: %4'ten fazla artmışsa UYAR (Dünkü kapanışa göre)
                    if real_change > 4.0: 
                        is_late = True
                        price_warning = f"⚠️ <b>DİKKAT:</b> {valid_ticker} bugün zaten <b>%{real_change:.2f}</b> prim yapmış! Tren kaçmış olabilir."
                        color_class = "warning"
                    else:
                        price_warning = f"✅ <b>Fiyat Uygun:</b> {valid_ticker} değişimi sadece %{real_change:.2f}. Henüz patlamamış."
                        
                # 2. Durum: Fiyat Verisi Çekilemedi (Hata)
                else:
                    price_warning = f"ℹ️ <b>Fiyat Çekilemedi:</b> Yapay zeka '{ticker_raw}' dedi ama borsada bulunamadı. Kodu manuel kontrol et."
                    color_class = "warning"

                # Kart Başlığı
                if is_late:
                    card_title = f"🚨 GEÇ KALDIN: {ticker_raw} (Riskli)"
                else:
                    card_title = f"💎 SİNYAL: {ticker_raw} ({s['Action']})"

                # HTML Kart Tasarımı
                html_card = f"""
                <div class="signal-card {color_class}">
                    <h3>{card_title}</h3>
                    <p><b>Güven Puanı:</b> %{s['Confidence']} | <b>Risk:</b> {s['Risk_Level']}</p>
                    
                    <div style="background-color: #333; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #555;">
                        {price_warning}
                    </div>
                    
                    <hr style="border-color: #555;">
                    <p>📝 <b>Neden:</b> {s['Reason']}</p>
                    <p>💰 <b>Kasa Planı:</b> {s['Entry_Plan']}</p>
                    <p>🛑 <b>Stop-Loss:</b> {s['Stop_Loss']} | 🎯 <b>Hedef:</b> {s['Target']}</p>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sistem Hatası: {e}")

# --- 9. BUTON ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("PİYASAYI ANALİZ ET 🚀", use_container_width=True):
        analyze_market()
