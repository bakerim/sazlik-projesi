import streamlit as st
import yfinance as yf
import pandas_ta as ta

# --- MERT'İN AVCI MODÜLÜ ---
def avci_sinyali_ver(symbol):
    try:
        # Veriyi çek (Son 3 ay)
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        if df.empty: return None

        # İndikatörleri Hesapla
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        # Son veriler
        last = df.iloc[-1]
        fiyat = float(last['Close'])
        rsi = float(last['RSI'])
        ema20 = float(last['EMA20'])
        
        # --- MANTIK (LOGIC) ---
        puan = 0
        if fiyat > ema20: puan += 40      # Trend bizden yana
        if 50 < rsi < 70: puan += 40      # Momentum var
        if rsi >= 70: puan += 10          # Çok güçlü ama riskli
        
        # KASA YÖNETİMİ
        if puan >= 80:
            ton = "MÜKEMMEL FIRSAT"
            kasa = 50
            renk = "success" # Yeşil
        elif puan >= 50:
            ton = "GÜÇLÜ AL"
            kasa = 25
            renk = "warning" # Sarı
        else:
            return None # Çöp hisse, gösterme bile.

        # HEDEF HESAPLA (%5 Kar, %2.5 Stop)
        hedef = round(fiyat * 1.05, 2)
        stop = round(fiyat * 0.975, 2)

        # --- ÇIKTI FORMATI (SENİN İSTEDİĞİN GİBİ) ---
        st.markdown(f"### 🚨 SİNYAL: {symbol} ({ton})")
        st.code(f"""
👉 EMİR: {symbol} HİSSESİ AL
💰 KASA KULLANIMI: %{kasa}

📉 GİRİŞ FİYATI: ${fiyat:.2f}
🎯 SATIŞ HEDEFİ: ${hedef} (%5 Kâr)
🛑 STOP LOSS:    ${stop}

⏳ VADE: 1-3 İş Günü
📊 GÖSTERGELER: RSI: {int(rsi)} | Sistem Puanı: {puan}
        """, language="yaml")
        
        if renk == "success":
            st.success(f"Sistem {symbol} için ateş ediyor! Güven: %{puan}")
        else:
            st.warning(f"Sistem {symbol} için temkinli. Güven: %{puan}")
            
    except Exception as e:
        st.error(f"Hata oluştu: {e}")

# --- ARAYÜZ ---
st.title("💸 SAZLIK - AVCI MODU")
st.write("Duygu yok. Sadece matematik.")

hisse = st.text_input("Hisse Sembolü Gir (Örn: AAPL, TSLA, BTC-USD):", "AAPL").upper()

if st.button("ANALİZ ET VE BANA NE YAPACAĞIMI SÖYLE"):
    avci_sinyali_ver(hisse)
