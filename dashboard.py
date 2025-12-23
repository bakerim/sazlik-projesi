import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık Avcı Modu", layout="centered")

# --- AVCI MODÜLÜ ---
def avci_sinyali_ver(symbol):
    try:
        # 1. Veriyi Çek (Son 6 ay ki EMA50 düzgün otursun)
        st.info(f"{symbol} için veriler borsadan çekiliyor...")
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        
        # Veri kontrolü
        if df is None or df.empty:
            st.error(f"❌ '{symbol}' için veri bulunamadı. Sembolü doğru yazdığından emin ol (Örn: THYAO.IS, AAPL, BTC-USD).")
            return

        # 2. Sütun İsimlerini Temizle (Bazen MultiIndex geliyor, düzeltelim)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Kapanış fiyatı kontrolü
        if 'Close' not in df.columns:
            st.error("❌ Veri çekildi ama 'Close' (Kapanış) sütunu eksik.")
            return

        # 3. İndikatörleri Hesapla (Hata olursa None dönmesini engelle)
        rsi = ta.rsi(df['Close'], length=14)
        ema20 = ta.ema(df['Close'], length=20)
        
        # İndikatörler hesaplanamadıysa dur
        if rsi is None or ema20 is None:
             st.error("⚠️ İndikatörler hesaplanamadı. Veri yetersiz olabilir.")
             return

        df['RSI'] = rsi
        df['EMA20'] = ema20
        
        # NaN (Boş) verileri temizle. En son dolu satırı alacağız.
        df_clean = df.dropna()
        
        if df_clean.empty:
            st.warning("⚠️ Yeterli tarihsel veri yok (İndikatörler için en az 20-30 gün lazım).")
            return

        # Son veriyi al
        last = df_clean.iloc[-1]
        
        # Değerleri güvenli şekilde al
        fiyat = float(last['Close'])
        rsi_val = float(last['RSI'])
        ema20_val = float(last['EMA20'])
        
        # --- MANTIK (LOGIC) ---
        puan = 0
        aciklama = []

        if fiyat > ema20_val: 
            puan += 40
            aciklama.append("Trend Yukarı (+40)")
        
        if 50 < rsi_val < 70: 
            puan += 40
            aciklama.append("Momentum Güçlü (+40)")
        elif rsi_val >= 70: 
            puan += 10
            aciklama.append("Aşırı Alım Bölgesi (+10)")
        else:
            aciklama.append("Momentum Zayıf (0)")
        
        # KASA YÖNETİMİ
        if puan >= 80:
            ton = "MÜKEMMEL FIRSAT"
            kasa = 50
            renk = "success"
        elif puan >= 40: # Eşiği biraz düşürdük test edebilmen için
            ton = "GÜÇLÜ AL"
            kasa = 25
            renk = "warning"
        else:
            st.error(f"⛔ SİNYAL YOK: {symbol} (Puan: {puan}) - Pas Geç.")
            st.write(f"Detay: {', '.join(aciklama)}")
            return 

        # HEDEF HESAPLA (%5 Kar, %2.5 Stop)
        hedef = round(fiyat * 1.05, 2)
        stop = round(fiyat * 0.975, 2)

        # --- ÇIKTI ---
        st.divider()
        st.markdown(f"### 🚨 SİNYAL: {symbol} ({ton})")
        
        # Renkli kutu içinde gösterim
        if renk == "success":
            st.success(f"SİSTEM PUANI: {puan} | GÜVEN: YÜKSEK")
        else:
            st.warning(f"SİSTEM PUANI: {puan} | GÜVEN: ORTA")

        st.code(f"""
👉 EMİR: {symbol} HİSSESİ AL
💰 KASA KULLANIMI: %{kasa}

📉 GİRİŞ FİYATI: ${fiyat:.2f}
🎯 SATIŞ HEDEFİ: ${hedef} (%5 Kâr)
🛑 STOP LOSS:    ${stop}

⏳ VADE: 1-3 İş Günü
📊 GÖSTERGELER: RSI: {int(rsi_val)} | EMA20: {ema20_val:.2f}
        """, language="yaml")
        
        st.caption(f"Analiz Detayı: {', '.join(aciklama)}")
            
    except Exception as e:
        st.error(f"Beklenmedik bir hata oluştu: {e}")
        # Hata ayıklama için detay (Gerekirse açarsın)
        # st.write(df.tail())

# --- ARAYÜZ ---
st.title("💸 SAZLIK - AVCI MODU")
st.write("Duygu yok. Sadece matematik.")

col1, col2 = st.columns([3, 1])
with col1:
    hisse = st.text_input("Hisse Sembolü (Örn: AAPL, TSLA, BTC-USD):", "AAPL").upper()
with col2:
    st.write("")
    st.write("")
    btn = st.button("ANALİZ ET")

if btn:
    avci_sinyali_ver(hisse)
