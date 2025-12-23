import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık Pro V4.1", layout="wide")

# --- LİSTE ---
WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE",
    "CRM", "QCOM", "TXN", "INTC", "CSCO", "NFLX", "ORCL", "MU", "AMD", 
    "JPM", "V", "MA", "BAC", "GS", "MS", "BLK", "C", "AXP", "PYPL", "COIN", "SQ",
    "JNJ", "LLY", "UNH", "PFE", "MRK", "AMGN", "GILD", "MRNA", "BIIB",
    "PG", "KO", "PEP", "WMT", "COST", "MCD", "NKE", "SBUX", "XOM", "CVX", "BA", "GE", "CAT",
    "UBER", "ABNB", "PLTR", "SOFI", "RBLX", "DKNG", "SHOP", "SPOT", "ROKU", "ZM", "DOCU",
    "ETSY", "ENPH", "SEDG", "LCID", "RIVN", "NIO", "BABA", "JD", "T", "VZ"
]

# --- MOTOR ---
def analiz_motoru(symbol):
    try:
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if 'Close' not in df.columns: return None

        # İndikatörler
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
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

        hareket_yuzdesi = (atr / fiyat) * 100
        
        # Hız Limiti: %1.5 altı çok yavaş, ele.
        if hareket_yuzdesi < 1.5: return None 

        # --- PUANLAMA ---
        puan = 0
        sebepler = []

        if fiyat > ema20:
            puan += 30
            sebepler.append("Trend Pozitif")
        
        if 50 <= rsi <= 65:
            puan += 30
            sebepler.append("RSI İdeal")
        elif 65 < rsi < 75:
            puan += 15
            sebepler.append("RSI Yüksek")
        
        if vol > vol_avg:
            puan += 20
            sebepler.append("Hacim Artışı")
            
        if hareket_yuzdesi > 2.5:
            puan += 20
            sebepler.append("Yüksek Hız")
        elif hareket_yuzdesi > 1.5:
            puan += 10

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
st.title("💸 SAZLIK V4.1 - RENKLİ AVCI")
st.write("Sadece en yüksek puanlı **TOP 10** hisse gösterilir.")
st.markdown("---")

col1, col2 = st.columns([1, 2])
with col1:
    bakiye = st.number_input("💵 Kasa ($):", min_value=100.0, value=1000.0, step=100.0)

if st.button("🚀 TARAMAYI BAŞLAT"):
    
    st.info("📡 Piyasa taranıyor... Renkler hazırlanıyor...")
    progress = st.progress(0)
    
    firsatlar = []
    for i, hisse in enumerate(WATCHLIST):
        progress.progress((i + 1) / len(WATCHLIST))
        sonuc = analiz_motoru(hisse)
        if sonuc:
            firsatlar.append(sonuc)
    progress.empty()
    
    if not firsatlar:
        st.error("❌ Piyasa kötü. Uygun hisse çıkmadı.")
    else:
        # Puan sıralaması ve İLK 10 FİLTRESİ
        firsatlar = sorted(firsatlar, key=lambda x: x['puan'], reverse=True)
        secilenler = firsatlar[:10] # Sadece Top 10
        
        # Ağırlıklı Dağıtım Hesabı (Sadece ekrandaki 10 hisse için)
        toplam_puan = sum(item['puan'] for item in secilenler)
        
        st.success(f"✅ En iyi {len(secilenler)} hisse listeleniyor.")
        st.markdown("---")
        
        # 3'lü kolon düzeni
        cols = st.columns(3)
        
        for i, veri in enumerate(secilenler):
            with cols[i % 3]:
                # 1. Renk Belirleme
                if veri['puan'] >= 90:
                    renk_str = "green"
                    baslik = "MÜKEMMEL"
                    emoji = "🟢"
                elif veri['puan'] >= 80:
                    renk_str = "blue"
                    baslik = "GÜÇLÜ"
                    emoji = "🔵"
                else:
                    renk_str = "orange"
                    baslik = "DENENEBİLİR"
                    emoji = "🟠"

                # 2. Hesaplamalar
                pay_orani = veri['puan'] / toplam_puan
                yatirim_tutari = bakiye * pay_orani
                giris = veri['fiyat']
                hedef = giris * 1.05
                stop = giris * 0.975
                
                # Süre Tahmini (Güvenlik payı eklenmiş)
                gun_tahmini = max(1, int(5 / veri['atr_pct']))
                vade_str = f"1-{gun_tahmini + 1} Gün"

                # 3. KART ÇİZİMİ
                # Başlığı Renkli Yapıyoruz
                st.markdown(f"### :{renk_str}[{emoji} {veri['symbol']}]")
                st.caption(f"**{baslik}** | Puan: {veri['puan']} | Hız: %{veri['atr_pct']:.2f}/gün")
                
                st.code(f"""
💰 YATIRIM: ${yatirim_tutari:.2f}
👉 EMİR: AL
📉 GİRİŞ: ${giris:.2f}
🎯 HEDEF: ${hedef:.2f}
🛑 STOP:  ${stop:.2f}
⏳ SÜRE:  {vade_str}
                """, language="yaml")
                
                st.markdown(f"*{', '.join(veri['sebepler'])}*")
                st.markdown("---")
