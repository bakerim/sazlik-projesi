import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import random

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık Avcı Modu", layout="centered")

# --- AVCI MODÜLÜ ---
def avci_sinyali_ver(symbol, test_modu=False):
    try:
        # --- TEST MODU İSE SAHTE VERİ ÜRET ---
        if test_modu:
            st.warning("⚠️ DİKKAT: BU BİR SİMÜLASYONDUR. GERÇEK VERİ DEĞİL.")
            fiyat = 150.00
            hedef = 157.50
            stop = 146.25
            rsi_val = 65
            ema20_val = 140.00
            puan = 90
            ton = "MÜKEMMEL FIRSAT"
            kasa = 50
            renk = "success"
            aciklama = ["Test: Trend Yukarı", "Test: Momentum Güçlü"]
            
        else:
            # --- GERÇEK MOD ---
            # 1. Veriyi Çek
            with st.spinner(f"{symbol} taranıyor..."):
                df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            
            # Veri kontrolü
            if df is None or df.empty:
                st.error(f"❌ '{symbol}' için veri bulunamadı.")
                return

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            if 'Close' not in df.columns:
                st.error("❌ Veri hatası: Kapanış fiyatı yok.")
                return

            # İndikatörler
            rsi = ta.rsi(df['Close'], length=14)
            ema20 = ta.ema(df['Close'], length=20)
            
            df['RSI'] = rsi
            df['EMA20'] = ema20
            df_clean = df.dropna()
            
            if df_clean.empty:
                st.warning("⚠️ Yeterli veri yok.")
                return

            last = df_clean.iloc[-1]
            fiyat = float(last['Close'])
            rsi_val = float(last['RSI'])
            ema20_val = float(last['EMA20'])
            
            # --- PUANLAMA ---
            puan = 0
            aciklama = []

            # Kriter 1: Trend
            if fiyat > ema20_val: 
                puan += 40
                aciklama.append("Trend Yukarı (+40)")
            else:
                aciklama.append("Fiyat Ortalamanın Altında (Trend Yok)")
            
            # Kriter 2: Momentum
            if 50 < rsi_val < 70: 
                puan += 40
                aciklama.append("Momentum İdeal (+40)")
            elif rsi_val >= 70: 
                puan += 10
                aciklama.append("Aşırı Alım (+10)")
            else:
                aciklama.append("Momentum Zayıf (RSI < 50)")
            
            # Kasa ve Renk Kararı
            if puan >= 80:
                ton = "MÜKEMMEL FIRSAT"
                kasa = 50
                renk = "success"
            elif puan >= 40:
                ton = "GÜÇLÜ AL"
                kasa = 25
                renk = "warning"
            else:
                # SİNYAL YOKSA BURADA KESİYORUZ
                st.error(f"⛔ SİNYAL YOK: {symbol} (Puan: {puan}) - Pas Geç.")
                st.info(f"Neden? -> {', '.join(aciklama)}")
                return 

            hedef = round(fiyat * 1.05, 2)
            stop = round(fiyat * 0.975, 2)

        # --- YEŞİL KUTU ÇIKTISI (KAZANDIRAN EKRAN) ---
        st.divider()
        st.markdown(f"### 🚨 SİNYAL: {symbol} ({ton})")
        
        if renk == "success":
            st.success(f"SİSTEM PUANI: {puan} | GÜVEN: YÜKSEK 🚀")
        else:
            st.warning(f"SİSTEM PUANI: {puan} | GÜVEN: ORTA ⚠️")

        st.code(f"""
👉 EMİR: {symbol} HİSSESİ AL
💰 KASA KULLANIMI: %{kasa}

📉 GİRİŞ FİYATI: ${fiyat:.2f}
🎯 SATIŞ HEDEFİ: ${hedef} (%5 Kâr)
🛑 STOP LOSS:    ${stop}

⏳ VADE: 1-3 İş Günü
📊 GÖSTERGELER: RSI: {int(rsi_val)} | EMA20: {ema20_val:.2f}
        """, language="yaml")
        
        if not test_modu:
            st.caption(f"Analiz Detayı: {', '.join(aciklama)}")
            
    except Exception as e:
        st.error(f"Hata: {e}")

# --- ARAYÜZ ---
st.title("💸 SAZLIK - AVCI MODU")
st.write("Duygu yok. Sadece matematik.")

col1, col2 = st.columns([3, 1])
with col1:
    hisse = st.text_input("Hisse Sembolü:", "AAPL").upper()
with col2:
    st.write("")
    st.write("")
    # BUTON
    btn = st.button("ANALİZ ET")

# TEST MODU KUTUSU
test_aktif = st.checkbox("🛠️ Simülasyon Modu (Kutuyu Görmek İçin Tıkla)")

if btn:
    avci_sinyali_ver(hisse, test_modu=test_aktif)
