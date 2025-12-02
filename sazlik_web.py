import streamlit as st
import google.generativeai as genai
import feedparser
import json
import time
import yfinance as yf

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık: SwingSniper", page_icon="🎯", layout="wide")

# --- 2. CSS İLE GÖRSELİ GÜZELLEŞTİRME ---
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .big-font {
        font-size:20px !important;
        color: #e0e0e0;
    }
    .signal-card {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid;
    }
    .success { background-color: #1e3a2f; border-color: #00ff00; }
    .warning { background-color: #3a2e1e; border-color: #ffaa00; }
</style>
""", unsafe_allow_html=True)

# --- 3. YARDIMCI FONKSİYON: FİYAT KONTROLÜ ---
def get_price_data(ticker):
    """
    Hissenin anlık fiyat değişimini kontrol eder.
    Eğer hisse çoktan uçmuşsa (Örn: %13) bizi uyarır.
    """
    try:
        # BIST hissesi mi Global mi anlamaya çalışalım
        # AI bazen düz verir, biz garanti olsun diye hem normal hem .IS deneriz.
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        
        # Eğer boş gelirse (muhtemelen BIST hissesi), sonuna .IS ekleyelim
        if hist.empty:
            stock = yf.Ticker(f"{ticker}.IS")
            hist = stock.history(period="1d")

        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[0]
            # Yüzdelik değişimi hesapla
            change_percent = ((current_price - open_price) / open_price) * 100
            return change_percent, current_price
        else:
            return None, None
    except:
        return None, None

# --- 4. KENAR ÇUBUĞU ---
with st.sidebar:
    st.title("🎛️ Kontrol Paneli")
    st.write("Sazlık Projesi - Web v3.1")
    
    # API Key girişi (Güvenlik için)
    api_key = st.text_input("Google Gemini API Key", type="password")
    
    st.divider()
    st.info("💡 **Garantici Mod Açık:**\nSistem global riskleri ve **anlık fiyat şişkinliğini** kontrol eder.")

# --- 5. ANA EKRAN ---
st.title("🎯 SwingSniper: Sazlık Projesi")
st.markdown("**Durum:** `Sistem Aktif` | **Mod:** `Defansif / Aile Babası`")

# --- 6. GELİŞMİŞ PROMPT (HATA DÜZELTİLDİ) ---
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

# --- 7. HABER KAYNAKLARI ---
RSS_URLS = [
    "https://tr.investing.com/rss/news_25.rss", # Borsa İstanbul Haberleri
    "https://tr.investing.com/rss/news_1.rss",  # Forex/Emtia Haberleri
    "https://finance.yahoo.com/news/rssindex"   # Global Kontrol
]

# --- 8. ANALİZ FONKSİYONU ---
def analyze_market():
    if not api_key:
        st.error("Lütfen sol menüden API Anahtarını gir.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=SYSTEM_PROMPT)

    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # A. Haberleri Çek
    status_text.text("📡 Piyasalar taranıyor (RSS)...")
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
        st.error("Haber kaynağına ulaşılamadı.")
        return

    # B. Analiz Et (AI)
    status_text.text(f"🧠 {len(all_headlines)} adet veri yapay zekaya gönderiliyor...")
    
    prompt = "Şu anki piyasa haberleri aşağıdadır. Protokole göre analiz et:\n" + "\n".join(all_headlines)
    
    try:
        response = model.generate_content(prompt)
        # JSON Temizliği
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        signals = json.loads(clean_text)
        
        status_text.text("✅ Analiz tamamlandı!")
        progress_bar.progress(100)
        time.sleep(1)
        status_text.empty() 
        
        # C. Sonuçları Göster
        if not signals:
            st.info("🤷‍♂️ **Şu an 'Garantici Protokol'e uyan net bir fırsat bulunamadı.** Piyasa ya çok riskli ya da haberler yetersiz.")
            with st.expander("Taranan Haberleri Gör"):
                for h in all_headlines:
                    st.write(h)
        else:
            for s in signals:
                ticker = s.get('Ticker', 'UNKNOWN')
                
                # --- D. FİYAT KONTROLÜ (BIST/GLOBAL) ---
                real_change, real_price = get_price_data(ticker)
                
                is_late = False
                price_warning = ""
                # Varsayılan renk
                color_class = "success" if s['Confidence'] > 85 else "warning"
                
                if real_change is not None:
                    # KURAL: %4'ten fazla artmışsa UYAR
                    if real_change > 4.0: 
                        is_late = True
                        price_warning = f"⚠️ <b>DİKKAT:</b> Hisse bugün zaten <b>%{real_change:.2f}</b> yükselmiş! Tren kaçmış olabilir, geri çekilme bekle."
                        color_class = "warning" # Rengi sarı/turuncu yap
                    else:
                        price_warning = f"✅ <b>Fiyat Uygun:</b> Günlük değişim sadece %{real_change:.2f}. Henüz patlamamış."
                else:
                    price_warning = "ℹ️ Anlık fiyat verisi çekilemedi (Ticker hatası olabilir, manuel kontrol et)."
                
                # Kart Başlığını Güncelle
                if is_late:
                    card_title = f"🚨 GEÇ KALDIN: {ticker} (Riskli Yükseliş)"
                else:
                    card_title = f"💎 SİNYAL: {ticker} ({s['Action']})"

                html_card = f"""
                <div class="signal-card {color_class}">
                    <h3>{card_title}</h3>
                    <p><b>Güven Puanı:</b> %{s['Confidence']} | <b>Risk:</b> {s['Risk_Level']}</p>
                    <div style="background-color: #333; padding: 10px; border-radius: 5px; margin: 10px 0;">
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
        st.error(f"Bir hata oluştu: {e}")
        with st.expander("Hata Detayı"):
            st.write(response.text if 'response' in locals() else "AI Yanıt Vermedi")

# --- 9. BUTON ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("PİYASAYI ANALİZ ET 🚀", use_container_width=True):
        analyze_market()
