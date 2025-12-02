import streamlit as st
import google.generativeai as genai
import feedparser
import json
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık: SwingSniper", page_icon="🎯", layout="wide")

# --- CSS İLE GÖRSELİ GÜZELLEŞTİRME (Siyah/Koyu Tema) ---
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

# --- KENAR ÇUBUĞU (API KEY GİRİŞİ) ---
with st.sidebar:
    st.title("🎛️ Kontrol Paneli")
    st.write("Sazlık Projesi - Web v3.0")
    
    # Güvenlik için API Key'i buradan alıyoruz, kodun içine gömmüyoruz.
    api_key = st.text_input("Google Gemini API Key", type="password")
    
    st.divider()
    st.info("💡 **Garantici Mod Açık:**\nSistem global riskleri (Nvidia, Savaş vb.) kontrol etmeden sinyal vermez.")

# --- ANA EKRAN ---
st.title("🎯 SwingSniper: Sazlık Projesi")
st.markdown("**Durum:** `Sistem Aktif` | **Mod:** `Defansif / Aile Babası`")

# --- GELİŞMİŞ "GARANTİCİ" PROMPT ---
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
4. **KASA YÖNETİMİ (Çok Önemli):** Asla "Tüm paranı bas" deme. Güvene göre kasanın %10'u veya en fazla %20'si ile işlem öner.

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

# --- HABER KAYNAKLARI (TEST İÇİN) ---
RSS_URLS = [
    "https://tr.investing.com/rss/news_25.rss", # Borsa İstanbul Haberleri
    "https://tr.investing.com/rss/news_1.rss",  # Forex/Emtia Haberleri
    "https://finance.yahoo.com/news/rssindex"   # Global Kontrol (İngilizce - AI anlar)
]

def analyze_market():
    if not api_key:
        st.error("Lütfen sol menüden API Anahtarını gir.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=SYSTEM_PROMPT)

    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # 1. Haberleri Çek
    status_text.text("📡 Piyasalar taranıyor (RSS)...")
    all_headlines = []
    
    for i, url in enumerate(RSS_URLS):
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Her kaynaktan son 5 haber
                all_headlines.append(f"- {entry.title} (Kaynak: {feed.feed.get('title', 'Web')})")
        except:
            pass
        progress_bar.progress((i + 1) / len(RSS_URLS))

    if not all_headlines:
        st.error("Haber kaynağına ulaşılamadı.")
        return

    # 2. Analiz Et (AI)
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
        status_text.empty() # Yazıyı temizle
        
        # 3. Sonuçları Göster
        if not signals:
            st.info("🤷‍♂️ **Şu an 'Garantici Protokol'e uyan net bir fırsat bulunamadı.** Piyasa ya çok riskli ya da haberler yetersiz.")
            with st.expander("Taranan Haberleri Gör"):
                for h in all_headlines:
                    st.write(h)
        else:
            for s in signals:
                # Renk belirleme
                color_class = "success" if s['Confidence'] > 85 else "warning"
                
                html_card = f"""
                <div class="signal-card {color_class}">
                    <h3>🚨 SİNYAL: {s['Ticker']} ({s['Action']})</h3>
                    <p><b>Güven Puanı:</b> %{s['Confidence']} | <b>Risk:</b> {s['Risk_Level']}</p>
                    <hr style="border-color: #555;">
                    <p>📝 <b>Neden:</b> {s['Reason']}</p>
                    <p>💰 <b>Kasa Planı:</b> {s['Entry_Plan']}</p>
                    <p>🛑 <b>Stop-Loss:</b> {s['Stop_Loss']} | 🎯 <b>Hedef:</b> {s['Target']}</p>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
        st.write("Ham Cevap:", response.text)

# --- BUTON ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("PİYASAYI ANALİZ ET 🚀", use_container_width=True):
        analyze_market()
