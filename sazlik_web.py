import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import requests
import json

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık AI 2.0", page_icon="🌾", layout="wide")

# --- API ANAHTARI KONTROLÜ (Streamlit Secrets) ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ API Anahtarı Bulunamadı! Streamlit panelinden 'Secrets' ayarını yapmalısın.")
    st.stop()

# --- 1. MODÜL: TEKNİK ANALİZ (GÖZ) ---
def get_technical_status(ticker):
    """
    Canlı piyasadan son fiyatı ve trend durumunu çeker.
    """
    try:
        # BIST kodu kontrolü (.IS ekleme)
        symbol = f"{ticker}.IS" if not ticker.endswith(".IS") else ticker
        
        # Son 1 aylık veri
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return None, "Veri Yok"
            
        price = hist['Close'].iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        
        # Basit Trend Analizi (Fiyat Ortalamanın neresinde?)
        if price > sma20 * 1.01:
            trend = "YÜKSELİŞ TRENDİ (Boğa) 🟢"
        elif price < sma20 * 0.99:
            trend = "DÜŞÜŞ TRENDİ (Ayı) 🔴"
        else:
            trend = "YATAY / KARARSIZ 🟡"
            
        return price, trend
    except Exception as e:
        return None, "Hata"

# --- 2. MODÜL: GERÇEK HAFIZA (RAG) ---
def get_past_context(ticker):
    """
    GitHub'daki news_archive.json dosyasını okur.
    Gerçek veriye dayalı hafıza modülü.
    """
    # Senin GitHub Repo Adresin (bakerim/sazlik-projesi)
    url = "https://raw.githubusercontent.com/bakerim/sazlik-projesi/main/news_archive.json"
    
    try:
        response = requests.get(url)
        
        if response.status_code != 200:
            return "⚠️ Arşiv dosyasına (news_archive.json) ulaşılamadı. Henüz oluşturmamış olabilirsin."
            
        data = response.json()
        
        # O hisseyle ilgili haberleri bul ve listele
        found_news = []
        for item in data:
            if item.get('ticker') == ticker:
                found_news.append(f"- [{item['date']}] {item['content']} (Duygu: {item.get('ai_sentiment', '-')})")
        
        if found_news:
            return "\n".join(found_news)
        else:
            return f"ℹ️ {ticker} için arşivde kayıtlı geçmiş veri yok."
            
    except json.JSONDecodeError:
        return "⚠️ JSON Format Hatası: Arşiv dosyasındaki parantezleri kontrol et."
    except Exception as e:
        return f"Hafıza Hatası: {str(e)}"

# --- 3. MODÜL: AI BEYNİ (GEMINI 2.0 FLASH) ---
def ask_gemini(ticker, price, trend, context, news_text):
    """
    Toplanan tüm verileri Gemini 2.0'a gönderir.
    """
    # En güncel ve hızlı model
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    SEN UZMAN BİR SWING TRADE VE RİSK ANALİSTİSİN.
    
    Aşağıdaki veri setini kullanarak detaylı bir analiz yap.

    1. VARLIK: {ticker}
    2. PİYASA GERÇEKLİĞİ (Teknik): Fiyat {price:.2f} TL | Durum: {trend}
    3. KURUMSAL HAFIZA (Geçmiş Haberler): 
    {context}
    
    4. FLAŞ GELİŞME (Yeni Haber): 
    "{news_text}"

    GÖREVİN:
    Bu yeni haberin fiyata etkisini ölç.
    Özellikle hafızadaki eski haberlerle bu yeni haber arasında bir bağlantı (devamlılık veya çelişki) varsa bunu mutlaka belirt.

    ÇIKTI FORMATI (Türkçe):
    1. Etki Skoru: (0-100 arası)
    2. Derin Analiz: (Teknik trend ve hafızayı harmanlayarak yapılmış yorum)
    3. Swing Sinyali: (Güçlü Al / Kademeli Al / İzle / Sat / Uzak Dur)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Bağlantı Hatası: {str(e)}"

# --- ARAYÜZ (UI) ---
st.title("🌾 Sazlık Projesi v2.0")
st.caption("Powered by Gemini 2.0 Flash & GitHub RAG Architecture")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Sinyal Paneli")
    ticker = st.text_input("Hisse Kodu (Örn: TKFEN, ASELS)", "TKFEN").upper()
    news = st.text_area("Haber / Duyum", height=150, placeholder="Yeni düşen haberi buraya yapıştır...")
    analyze_btn = st.button("Analiz Et (Gemini 2.0)", type="primary")

with col2:
    if analyze_btn:
        if not ticker or not news:
            st.warning("Lütfen hisse kodu ve haber metni girin.")
        else:
            with st.spinner(f"{ticker} için piyasa ve arşiv taranıyor..."):
                # 1. Teknik Veri
                price, trend = get_technical_status(ticker)
                
                if price:
                    # Metrik Gösterimi
                    m1, m2 = st.columns(2)
                    m1.metric("Anlık Fiyat", f"{price:.2f} TL")
                    m2.metric("Trend Yönü", trend)
                    
                    st.divider()
                    
                    # 2. Hafıza (RAG) - Gerçek GitHub Dosyası
                    context = get_past_context(ticker)
                    with st.expander(f"📂 {ticker} Arşiv Kayıtları (Hafıza)"):
                        if "Arşiv dosyasına ulaşılamadı" in context:
                            st.warning(context)
                            st.caption("GitHub ana dizininde 'news_archive.json' dosyasını oluşturmalısın.")
                        else:
                            st.info(context)
                    
                    # 3. AI Analizi
                    result = ask_gemini(ticker, price, trend, context, news)
                    
                    st.markdown("### 🤖 Yapay Zeka Kararı")
                    st.success("Analiz Tamamlandı")
                    st.markdown(result)
                else:
                    st.error("Hisse bulunamadı. Kodu doğru girdiğinden emin ol.")

# Alt Bilgi
st.markdown("---")
st.caption("Sazlık Yatırım Asistanı - Bilimsel Veri Analizi")
