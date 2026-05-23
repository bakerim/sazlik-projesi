import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import config 

st.set_page_config(page_title="Sazlık V4 - Kurumsal Terminal", layout="wide")

WATCHLIST = sorted(list(set(getattr(config, 'WATCHLIST_TICKERS', ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "WAB", "DE", "FSLY", "DVA", "KO", "PG", "JNJ", "EOG", "INTU"]))))

if 'v3_sonuclar' not in st.session_state: st.session_state['v3_sonuclar'] = []
if 'amiral_sonuclar' not in st.session_state: st.session_state['amiral_sonuclar'] = []

st.markdown("""
<style>
.stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.main-title { font-size: 28px; font-weight: 600; color: #ffffff; margin-bottom: 25px; border-bottom: 1px solid #30363d; padding-bottom: 10px;}
.guven-header { background-color: #1f4287; color: white; padding: 10px; border-radius: 4px; font-weight: 600; font-size: 16px; margin-bottom: 15px;}
.amiral-header { background-color: #005a32; color: white; padding: 10px; border-radius: 4px; font-weight: 600; font-size: 16px; margin-bottom: 15px;}
.sazlik-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; margin-bottom: 15px;}
.amiral-card { background-color: #111b15; border: 1px solid #1a3a26; border-radius: 6px; padding: 16px; margin-bottom: 15px; border-left: 4px solid #2ea043;}
.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;}
.ticker-name { font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: 0.5px;}
.sector-badge { background-color: #2ea043; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold; margin-left: 8px; vertical-align: middle;}
.yakit-g { color: #3fb950; font-size: 12px; font-weight: 600; text-align: right;}
.yakit-y { color: #d29922; font-size: 12px; font-weight: 600; text-align: right;}
.data-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 12px;}
.data-label { font-size: 10px; color: #8b949e; text-transform: uppercase; font-weight: 600;}
.data-val { font-size: 15px; font-weight: 600; color: #ffffff; margin-top: 2px;}
.potansiyel-bar { background-color: #1c2b44; color: #8ab4f8; padding: 8px 12px; border-radius: 4px; font-size: 13px; font-weight: 500;}
.ai-verdict { background-color: #14221b; color: #7ee787; padding: 8px 12px; border-radius: 4px; font-size: 12px; margin-top: 10px; border: 1px solid #2ea043;}
.macro-warning { background-color: #4a0f0f; color: #ff7b72; padding: 12px; border-radius: 4px; border: 1px solid #f85149; margin-bottom: 20px; font-weight: 600; font-size: 14px;}
.macro-safe { background-color: #0f3d1b; color: #7ee787; padding: 12px; border-radius: 4px; border: 1px solid #2ea043; margin-bottom: 20px; font-weight: 600; font-size: 14px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">SAZLIK ANALİZ TERMİNALİ</div>', unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
def makro_piyasa_durumu():
    try:
        spy = yf.Ticker('SPY').history(period='3mo')['Close']
        if len(spy) < 50: return True
        return spy.iloc[-1] > spy.rolling(50).mean().iloc[-1]
    except: return True

if makro_piyasa_durumu():
    st.markdown('<div class="macro-safe">SİSTEM DURUMU: S&P 500 Endeksi yükseliş eğiliminde (SMA50 Üzeri). Makro görünüm pozitif.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="macro-warning">SİSTEM DURUMU: S&P 500 Endeksi düşüş eğiliminde (SMA50 Altı). Risk yönetimine dikkat ediniz.</div>', unsafe_allow_html=True)

# --- TEKNİK MOTOR (Güven Masası) ---
# DİKKAT: Gerçek zamanlı UI güncellemesi için st.cache_data KALDIRILDI!
def v3_guven_motoru(ticker_list, p_bar):
    sonuclar = []
    try:
        p_bar.progress(0.1, text="Tüm piyasa verileri paket halinde indiriliyor...")
        data = yf.download(ticker_list, period="3mo", progress=False)['Close']
        vol_data = yf.download(ticker_list, period="3mo", progress=False)['Volume']
        
        if isinstance(data, pd.Series): data = pd.DataFrame({ticker_list[0]: data})
        if isinstance(vol_data, pd.Series): vol_data = pd.DataFrame({ticker_list[0]: vol_data})
        
        for i, ticker in enumerate(ticker_list):
            # GERÇEK ZAMANLI BAR HESAPLAMASI (İndirme %20, İşleme %80 ağırlıkta)
            progress_oran = 0.2 + (0.8 * ((i + 1) / len(ticker_list)))
            p_bar.progress(progress_oran, text=f"İşleniyor: {ticker} (Doğrusallık ve Hacim Motoru)")
            
            if ticker not in data.columns: continue
            df = pd.DataFrame({'Close': data[ticker], 'Volume': vol_data[ticker]}).dropna()
            if len(df) < 30: continue
            
            curr = df['Close'].iloc[-1]
            vol_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            yakit_durumu = "YÜKSEK HACİM" if df['Volume'].tail(3).mean() > (vol_sma20 * 1.1) else "STANDART HACİM"
            
            y = df['Close'].tail(20).values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            r2 = 1 - (np.sum((y - (slope * x + intercept)) ** 2) / np.sum((y - np.mean(y)) ** 2)) if np.sum((y - np.mean(y)) ** 2) != 0 else 0
            hiz = (slope / curr) * 100
            
            if slope > 0.05 and r2 >= 0.70:
                puan_g = min(100, int((r2 * 70) + (20 if yakit_durumu == "YÜKSEK HACİM" else 0) + (10 if curr > df['Close'].rolling(50).mean().iloc[-1] else 0)))
                hedef_oran = 1.04 + (hiz / 100 * 2) 
                sonuclar.append({"ticker": ticker, "price": curr, "r2": r2, "slope": slope, "puan": puan_g, "yakit": yakit_durumu, "target": curr * hedef_oran, "stop": curr * 0.965, "pot_dolar": (curr * hedef_oran) - curr, "pot_yuzde": (hedef_oran - 1) * 100})
    except: pass
    
    p_bar.empty() # İşlem bitince barı ekrandan temizle
    return sorted(sonuclar, key=lambda x: x['puan'], reverse=True)

# --- EKONOMETRİK MOTOR (Amiral Masası) ---
# DİKKAT: Gerçek zamanlı UI güncellemesi için st.cache_data KALDIRILDI!
def amiral_ekonometri_motoru(ticker_list, p_bar):
    sonuclar = []
    
    for i, ticker in enumerate(ticker_list):
        # GERÇEK ZAMANLI BAR HESAPLAMASI (Her hissede yüzdelik dilim artar)
        progress_oran = (i + 1) / len(ticker_list)
        p_bar.progress(progress_oran, text=f"Bilanço taranıyor: {ticker} (F/K, PEG, Borç Rasyoları)")
        
        try:
            info = yf.Ticker(ticker).info
            if not info: continue
            fk = info.get('trailingPE', 0)
            if not (0 < fk < 35): continue
            
            sector = info.get('sector', 'N/A')
            peg = info.get('pegRatio', 99)
            borc = info.get('debtToEquity', 999) 
            roe = info.get('returnOnEquity', 0) * 100
            beta = info.get('beta', 1.5)
            fiyat = info.get('currentPrice', info.get('previousClose', 0))
            
            dy_raw = info.get('dividendYield', 0)
            if dy_raw is None: dy_raw = 0
            temettu = (dy_raw / 100) * 100 if dy_raw > 1 else dy_raw * 100
            if temettu > 25: temettu = 0 
            
            hist = yf.Ticker(ticker).history(period='1mo')['Close']
            if len(hist) < 20: continue
            delta = hist.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
            rs = gain / loss if loss != 0 else 0
            rsi = 100 - (100 / (1 + rs)) if loss != 0 else 100
            
            peg_p = 0 if peg <= 0 else (20 if peg <= 1.0 else (0 if peg >= 3.0 else 20 - ((peg - 1.0) / 2.0) * 20))
            borc_p = 20 if borc <= 20 else (0 if borc >= 150 else 20 - ((borc - 20) / 130) * 20)
            roe_p = 20 if roe >= 25 else (0 if roe <= 5 else ((roe - 5) / 20) * 20)
            beta_p = 10 if beta <= 0.8 else (0 if beta >= 1.5 else 10 - ((beta - 0.8) / 0.7) * 10)
            temettu_p = 10 if temettu >= 4.0 else (temettu / 4.0) * 10
            
            if 40 <= rsi <= 50: rsi_p = 20
            elif rsi > 70: rsi_p = max(0, 20 - (rsi - 50) * 0.8)
            elif rsi < 40: rsi_p = max(0, 20 - (40 - rsi) * 0.5)
            else: rsi_p = max(0, 20 - abs(rsi - 45) * 0.5)
            
            toplam_puan = int(peg_p + borc_p + roe_p + beta_p + temettu_p + rsi_p)
            
            verdict = []
            if peg_p > 15: verdict.append("İskontolu değerleme.")
            if borc_p > 15: verdict.append("Düşük borçluluk oranı.")
            if roe_p > 15: verdict.append("Yüksek özsermaye kârlılığı.")
            if rsi_p < 5: verdict.append("Aşırı alım bölgesinde (Dikkat).")
            
            if toplam_puan >= 50:
                ozet_metin = " | ".join(verdict) if verdict else "Dengeli finansal rasyolar."
                sonuclar.append({
                    "ticker": ticker, "sector": sector, "fiyat": fiyat, "fk": fk, "peg": peg, 
                    "roe": roe, "borc": borc, "beta": beta, "temettu": temettu, 
                    "rsi": rsi, "puan": toplam_puan, "verdict": ozet_metin
                })
        except Exception: continue
    
    p_bar.empty() # İşlem bitince barı ekrandan temizle
    return sorted(sonuclar, key=lambda x: x['puan'], reverse=True)

tab_guven, tab_amiral = st.tabs(["GÜVEN MASASI (Teknik Tarama)", "AMİRAL MASASI (Temel Analiz)"])

with tab_guven:
    if st.button("TARAMAYI BAŞLAT", use_container_width=True, key="btn_guven"):
        progress_bar = st.progress(0.0, text="Hazırlanıyor...")
        st.session_state['v3_sonuclar'] = v3_guven_motoru(WATCHLIST, progress_bar)
        
    if st.session_state['v3_sonuclar']:
        cols = st.columns(2)
        for idx, r in enumerate(st.session_state['v3_sonuclar'][:10]):
            yakit = f"<div class='yakit-g'>{r['yakit']}</div>" if r['yakit']=="YÜKSEK HACİM" else f"<div class='yakit-y'>{r['yakit']}</div>"
            html = f"""<div class="sazlik-card"><div class="card-top"><div class="ticker-name">{r['ticker']}</div>{yakit}</div>
            <div class="data-grid"><div><div class="data-label">ANALİTİK SKOR</div><div class="data-val">{r['puan']}</div></div><div><div class="data-label">R² DEĞERİ</div><div class="data-val">{r['r2']:.2f}</div></div><div><div class="data-label">TREND EĞİMİ</div><div class="data-val">{r['slope']:.2f}</div></div></div>
            <div class="data-grid"><div><div class="data-label">GİRİŞ SEVİYESİ</div><div class="data-val">${r['price']:.2f}</div></div><div><div class="data-label">KÂR HEDEFİ</div><div class="data-val" style="color:#81c995;">${r['target']:.2f}</div></div><div><div class="data-label">ZARAR KES</div><div class="data-val" style="color:#f28b82;">${r['stop']:.2f}</div></div></div>
            <div class="potansiyel-bar">Potansiyel Getiri Marjı: +${r['pot_dolar']:.2f} (%{r['pot_yuzde']:.2f})</div></div>"""
            with cols[idx % 2]: st.markdown(html, unsafe_allow_html=True)

with tab_amiral:
    if st.button("ANALİZİ BAŞLAT", type="primary", use_container_width=True, key="btn_amiral"):
        progress_bar = st.progress(0.0, text="Ekonometrik veritabanına bağlanılıyor...")
        st.session_state['amiral_sonuclar'] = amiral_ekonometri_motoru(WATCHLIST, progress_bar)
        
    if st.session_state['amiral_sonuclar']:
        cols_a = st.columns(2)
        for idx, r in enumerate(st.session_state['amiral_sonuclar'][:10]):
            html = f"""<div class="amiral-card"><div class="card-top"><div><span class="ticker-name" style="color:#2ea043;">{r['ticker']}</span><span class="sector-badge">{r['sector']}</span><div style="font-size:15px; color:#8b949e; margin-top:4px;">${r['fiyat']:.2f}</div></div><div style="text-align:right;"><div style="font-size:10px; color:#8b949e; font-weight:bold;">ANALİTİK SKOR</div><div style="font-size:24px; font-weight:700; color:#2ea043; margin-top:2px;">{r['puan']}</div></div></div>
            <div class="data-grid"><div><div class="data-label">F/K RASYOSU</div><div class="data-val">{r['fk']:.1f}</div></div><div><div class="data-label">RSI İNDİKATÖRÜ</div><div class="data-val" style="color:{'#ff7b72' if r['rsi']>70 else '#7ee787'};">{r['rsi']:.1f}</div></div><div><div class="data-label">ÖZSERMAYE KÂRLILIĞI</div><div class="data-val">%{r['roe']:.1f}</div></div></div>
            <div class="data-grid"><div><div class="data-label">BORÇ / ÖZKAYNAK</div><div class="data-val">%{r['borc']:.1f}</div></div><div><div class="data-label">BETA KATSAYISI</div><div class="data-val">{r['beta']:.2f}</div></div><div><div class="data-label">TEMETTÜ VERİMİ</div><div class="data-val" style="color:#e3b341;">%{r['temettu']:.1f}</div></div></div>
            <div class="ai-verdict"><b>Analiz Özeti:</b> {r['verdict']}</div></div>"""
            with cols_a[idx % 2]: st.markdown(html, unsafe_allow_html=True)