import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık Avcı Terminali", layout="wide")

# --- SENİN VERDİĞİN LİSTE (Temizlenmiş) ---
WATCHLIST = [
    # Teknoloji Devleri
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE",
    "CRM", "QCOM", "TXN", "INTC", "CSCO", "NFLX", "ORCL", "MU", "AMD", 
    # Finans
    "JPM", "V", "MA", "BAC", "GS", "MS", "BLK", "C", "AXP", "PYPL", "COIN", "SQ",
    # Sağlık & İlaç
    "JNJ", "LLY", "UNH", "PFE", "MRK", "AMGN", "GILD", "MRNA", "BIIB",
    # Tüketim & Enerji & Sanayi
    "PG", "KO", "PEP", "WMT", "COST", "MCD", "NKE", "SBUX", "XOM", "CVX", "BA", "GE", "CAT",
    # Diğer Büyüme & Trend
    "UBER", "ABNB", "PLTR", "SOFI", "RBLX", "DKNG", "SHOP", "SPOT", "ROKU", "ZM", "DOCU",
    "ETSY", "ENPH", "SEDG", "LCID", "RIVN", "NIO", "BABA", "JD", "T", "VZ"
]

# --- FONKSİYONLAR ---

def hisse_analiz_et(symbol):
    """Tek bir hisseyi analiz eder ve puanlar."""
    try:
        # Son 3 ayın verisi yeterli (Hız için)
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if 'Close' not in df.columns: return None

        # İndikatörler
        rsi = ta.rsi(df['Close'], length=14)
        ema20 = ta.ema(df['Close'], length=20) # Trend Çizgisi
        
        # Son Veriler
        df['RSI'] = rsi
        df['EMA20'] = ema20
        df = df.dropna()

        if df.empty: return None
        
        last = df.iloc[-1]
        fiyat = float(last['Close'])
        rsi_val = float(last['RSI'])
        ema20_val = float(last['EMA20'])
        prev_close = float(df.iloc[-2]['Close'])

        # --- PUANLAMA MOTORU (ALGORİTMA) ---
        puan = 0
        sebepler = []

        # 1. TREND: Fiyat EMA20'nin üzerinde mi? (Kısa vade yükseliş)
        if fiyat > ema20_val:
            puan += 40
            sebepler.append("Trend Yukarı")
        
        # 2. MOMENTUM: RSI ideal bölgede mi? (50-70 arası en tatlı yer)
        if 50 < rsi_val < 70:
            puan += 40
            sebepler.append("Momentum Güçlü")
        elif rsi_val >= 70:
            puan += 10
            sebepler.append("Aşırı Alım (Riskli)")
        
        # 3. GÜÇ: Düne göre artıda mı?
        if fiyat > prev_close:
            puan += 20
            sebepler.append("Yeşil Mum")

        # FİLTRE: Sadece 70 Puan ve üzerini ciddiye al
        if puan < 70: return None

        return {
            "symbol": symbol,
            "fiyat": fiyat,
            "puan": puan,
            "rsi": rsi_val,
            "ema": ema20_val,
            "sebepler": sebepler
        }

    except:
        return None

def kasa_yonetimi(bakiye):
    """Bakiyeye göre kaç hisse alınacağını belirler."""
    if bakiye <= 250:
        return 2, "Başlangıç"
    elif bakiye <= 500:
        return 4, "Orta Seviye"
    elif bakiye <= 1000:
        return 7, "Agresif Büyüme"
    else:
        return 10, "Balina"

# --- ARAYÜZ ---
st.title("💸 SAZLIK - OTOMATİK AVCI MODU")
st.markdown("---")

# 1. KASA GİRİŞİ
col_kasa, col_btn = st.columns([2, 1])
with col_kasa:
    bakiye = st.number_input("💵 Toplam Kasan (Dolar):", min_value=100, value=500, step=50)

# Kasa Mantığı
hisse_sayisi, seviye = kasa_yonetimi(bakiye)
bakiye_per_hisse = bakiye / hisse_sayisi

st.info(f"📋 STRATEJİ: **{seviye}** | Önerilecek Hisse Sayısı: **{hisse_sayisi}** | Hisse Başına Düşen Pay: **${bakiye_per_hisse:.2f}**")

# BUTON
if st.button("🚀 PİYASAYI TARA VE FIRSATLARI GETİR"):
    
    st.write("📡 Sazlık uydusu piyasayı tarıyor... (Bu işlem 30-40 saniye sürebilir)")
    progress_bar = st.progress(0)
    
    firsatlar = []
    
    # Tarama Döngüsü
    total_stocks = len(WATCHLIST)
    for i, hisse in enumerate(WATCHLIST):
        # Progress bar güncelle
        progress_bar.progress((i + 1) / total_stocks)
        
        # Analiz et
        sonuc = hisse_analiz_et(hisse)
        if sonuc:
            firsatlar.append(sonuc)
        
        # API limitine takılmamak için minik bekleme (Opsiyonel)
        # time.sleep(0.1) 

    progress_bar.empty()
    
    if not firsatlar:
        st.error("😔 Şu an kriterlerine uyan (Puanı 70+) hisse bulunamadı. Piyasa kötü olabilir.")
    else:
        # Puanına göre sırala (En yüksek puan en üstte)
        firsatlar = sorted(firsatlar, key=lambda x: x['puan'], reverse=True)
        
        # Sadece bütçenin izin verdiği kadarını al (Top X)
        secilenler = firsatlar[:hisse_sayisi]
        
        st.success(f"🎉 TARAMA BİTTİ! Toplam {len(firsatlar)} fırsat bulundu. En iyi {len(secilenler)} tanesi listeleniyor.")
        st.markdown("---")

        # SONUÇLARI KART OLARAK BAS
        cols = st.columns(3) # 3'lü ızgara görünümü
        
        for index, veri in enumerate(secilenler):
            with cols[index % 3]: # Izgaraya yerleştir
                # Hedef Hesaplamaları
                giris = veri['fiyat']
                hedef = giris * 1.05
                stop = giris * 0.975
                adet = int(bakiye_per_hisse / giris) 
                if adet < 1: adet = 1 # En az 1 tane al

                st.markdown(f"### 🚨 {veri['symbol']}")
                st.caption(f"Sistem Puanı: {veri['puan']} | {', '.join(veri['sebepler'])}")
                
                # Kart İçeriği
                st.code(f"""
👉 EMİR: AL
📦 ADET: ~{adet} Lot
💵 GİRİŞ: ${giris:.2f}
🎯 HEDEF: ${hedef:.2f} (%5)
🛑 STOP:  ${stop:.2f}
⏳ VADE:  1-10 Gün
📊 RSI:   {int(veri['rsi'])}
                """, language="yaml")
                
                if veri['puan'] >= 90:
                    st.success("MÜKEMMEL FIRSAT")
                else:
                    st.warning("GÜÇLÜ AL")
                
                st.markdown("---")
