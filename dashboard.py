import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık Pro V4 - Akıllı Dağıtım", layout="wide")

# --- LİSTE (BÜYÜK LİSTE) ---
WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE",
    "CRM", "QCOM", "TXN", "INTC", "CSCO", "NFLX", "ORCL", "MU", "AMD", 
    "JPM", "V", "MA", "BAC", "GS", "MS", "BLK", "C", "AXP", "PYPL", "COIN", "SQ",
    "JNJ", "LLY", "UNH", "PFE", "MRK", "AMGN", "GILD", "MRNA", "BIIB",
    "PG", "KO", "PEP", "WMT", "COST", "MCD", "NKE", "SBUX", "XOM", "CVX", "BA", "GE", "CAT",
    "UBER", "ABNB", "PLTR", "SOFI", "RBLX", "DKNG", "SHOP", "SPOT", "ROKU", "ZM", "DOCU",
    "ETSY", "ENPH", "SEDG", "LCID", "RIVN", "NIO", "BABA", "JD", "T", "VZ"
]

# --- FONKSİYONLAR ---

def analiz_motoru(symbol):
    try:
        # Veri Çek
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if 'Close' not in df.columns: return None

        # İndikatörler
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        # Hacim Ortalaması (Son 14 gün)
        df['Vol_Avg'] = df['Volume'].rolling(14).mean()

        df = df.dropna()
        if df.empty: return None
        
        last = df.iloc[-1]
        
        fiyat = float(last['Close'])
        rsi = float(last['RSI'])
        ema20 = float(last['EMA20'])
        atr = float(last['ATR'])
        vol = float(last['Volume'])
        vol_avg = float(last['Vol_Avg'])

        # --- HIZ KONTROLÜ (Volatilite) ---
        # Hisse günde ortalama % kaç oynuyor?
        hareket_yuzdesi = (atr / fiyat) * 100
        
        # Eğer hisse günde %1.5'tan az oynuyorsa (Çok hantalsa) ele.
        # Çünkü hantal hissede %5 kâr 10 günde gelmez.
        if hareket_yuzdesi < 1.5: 
            return None 

        # --- PUANLAMA (ZORLAŞTIRILMIŞ) ---
        puan = 0
        sebepler = []

        # 1. TREND (30 Puan): Fiyat EMA20 üstünde mi?
        if fiyat > ema20:
            puan += 30
            sebepler.append("Trend Pozitif")
        
        # 2. MOMENTUM (30 Puan): RSI 50-65 arası (Güçlü ama şişmemiş)
        if 50 <= rsi <= 65:
            puan += 30
            sebepler.append("RSI İdeal Bölge")
        elif 65 < rsi < 75:
            puan += 15 # Puan kırıyoruz, çünkü şişmeye başlamış
            sebepler.append("RSI Yüksek (Risk)")
        
        # 3. HACİM (20 Puan): Bugün ilgi var mı?
        if vol > vol_avg:
            puan += 20
            sebepler.append("Hacim Artışı")
            
        # 4. VOLATİLİTE (20 Puan): Hızlı mı?
        if hareket_yuzdesi > 2.5: # Çok hızlıysa ek puan
            puan += 20
            sebepler.append("Yüksek Volatilite (Hızlı Kâr)")
        elif hareket_yuzdesi > 1.5:
            puan += 10
            sebepler.append("Orta Volatilite")

        # FİLTRE: Sadece 70+ Puanı Göster
        if puan < 70: return None

        return {
            "symbol": symbol,
            "fiyat": fiyat,
            "puan": puan,
            "rsi": rsi,
            "atr_pct": hareket_yuzdesi,
            "sebepler": sebepler
        }

    except:
        return None

# --- ARAYÜZ ---
st.title("💸 SAZLIK V4 - AKILLI DAĞITIM")
st.markdown("---")

# KASA GİRİŞİ
col1, col2 = st.columns([2,2])
with col1:
    bakiye = st.number_input("💵 Toplam Kasan ($):", min_value=100.0, value=1000.0, step=100.0)

with col2:
    risk_modu = st.selectbox("🎯 Strateji Seç:", ["Dengeli (Max 5 Hisse)", "Sniper (Max 2 Hisse)"])

max_hisse = 5 if "Dengeli" in risk_modu else 2

if st.button("🔎 DERİN ANALİZ BAŞLAT"):
    
    st.info("📡 Piyasa taranıyor... Hantal hisseler eleniyor... Vidalar sıkılıyor...")
    progress = st.progress(0)
    
    firsatlar = []
    
    # Tarama
    for i, hisse in enumerate(WATCHLIST):
        progress.progress((i + 1) / len(WATCHLIST))
        sonuc = analiz_motoru(hisse)
        if sonuc:
            firsatlar.append(sonuc)
            
    progress.empty()
    
    if not firsatlar:
        st.error("❌ Kriterlere uyan hisse bulunamadı. Piyasa ya çok durgun ya da düşüşte.")
    else:
        # Puanına göre sırala
        firsatlar = sorted(firsatlar, key=lambda x: x['puan'], reverse=True)
        # En iyi X tanesini al
        secilenler = firsatlar[:max_hisse]
        
        # --- AĞIRLIKLI DAĞITIM HESABI ---
        toplam_puan = sum(item['puan'] for item in secilenler)
        
        st.success(f"✅ TARAMA TAMAMLANDI: {len(firsatlar)} adaydan en iyi {len(secilenler)} tanesi seçildi.")
        st.caption(f"💡 Dağıtım Mantığı: Puanı yüksek olana daha fazla bütçe ayrıldı.")
        st.markdown("---")
        
        cols = st.columns(len(secilenler))
        
        for i, veri in enumerate(secilenler):
            with cols[i]:
                # Pay Hesabı
                pay_orani = veri['puan'] / toplam_puan
                yatirim_tutari = bakiye * pay_orani
                
                # Hedefler
                giris = veri['fiyat']
                hedef = giris * 1.05
                stop = giris * 0.975
                
                # Tahmini Süre Hesabı (ATR'ye göre)
                # %5 hareket için kaç gün lazım? (Basit mantık: 5 / Günlük Hareket)
                gun_tahmini = max(1, int(5 / veri['atr_pct']))
                vade_str = f"1-{gun_tahmini+1} Gün"

                # KUTU RENGİ
                renk = "green" if veri['puan'] >= 90 else "orange"
                if veri['puan'] >= 90: baslik = "MÜKEMMEL" 
                else: baslik = "GÜÇLÜ"

                st.markdown(f"### :{renk}[{veri['symbol']}]")
                st.caption(f"Puan: {veri['puan']} | Hız: %{veri['atr_pct']:.2f}/gün")
                
                st.code(f"""
💰 YATIRIM: ${yatirim_tutari:.2f}
📊 PORTFÖY PAYI: %{pay_orani*100:.1f}

👉 EMİR: AL (Parçalı)
📉 GİRİŞ: ${giris:.2f}
🎯 HEDEF: ${hedef:.2f}
🛑 STOP:  ${stop:.2f}
⏳ SÜRE:  {vade_str}
                """, language="yaml")
                
                st.write(f"**Neden?** {', '.join(veri['sebepler'])}")
