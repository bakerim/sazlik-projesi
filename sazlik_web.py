import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import json
import os
from datetime import datetime
import config 

# --- 1. AYARLAR VE GÜVENLİK ---
st.set_page_config(page_title="Sazlık Master Terminal", page_icon="🦅", layout="wide")

# Config'den listeyi çek, tekrar edenleri temizle ve sırala
WATCHLIST = sorted(list(set(config.WATCHLIST_TICKERS)))

# --- 2. JSON VERİ YÖNETİMİ (KİŞİYE ÖZEL HAFIZA) ---
def get_portfolio_file(user): 
    return f"portfolio_{user}.json"

def load_portfolio(user):
    file_path = get_portfolio_file(user)
    if os.path.exists(file_path):
        with open(file_path, "r") as f: 
            return json.load(f)
    return []

def save_portfolio(user, data):
    with open(get_portfolio_file(user), "wb") as f: 
        f.write(json.dumps(data, indent=4).encode("utf-8"))

# --- 3. SESSION STATE (BELLEK) ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'current_user' not in st.session_state: st.session_state['current_user'] = None
if 'portfolio' not in st.session_state: st.session_state['portfolio'] = []
if 'last_results' not in st.session_state: st.session_state['last_results'] = []

# --- 4. GİRİŞ PANELİ ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center; color: #8ab4f8;'>🦅 Sazlık Terminal V23</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Kullanıcı").lower()
            p = st.text_input("Şifre", type="password")
            if st.form_submit_button("Sisteme Bağlan", use_container_width=True):
                if u in ['mert', 'murat'] and p == '1234':
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.session_state['portfolio'] = load_portfolio(u)
                    st.rerun()
                else:
                    st.error("Giriş Başarısız! Kullanıcı adı veya şifre hatalı.")
    st.stop()

# --- 5. GOOGLE FINANCE STİLİ CSS ---
st.markdown("""
<style>
    .stApp { background-color: #202124; color: #e8eaed; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #292a2d; border: 1px solid #3c4043; border-radius: 8px; padding: 15px; }
    .header-box { padding: 10px; border-bottom: 1px solid #3c4043; font-size: 18px; font-weight: 500; margin-bottom: 15px;}
    .guven-h { border-left: 4px solid #8ab4f8; }
    .amiral-h { border-left: 4px solid #f28b82; }
    .data-row { display: flex; justify-content: space-between; border-bottom: 1px solid #3c4043; padding: 8px 0; font-size: 14px;}
    .data-label { color: #9aa0a6; }
    .data-val { color: #e8eaed; font-weight: 500;}
</style>
""", unsafe_allow_html=True)

# --- 6. MATEMATİKSEL MOTOR (Garantici Baba'nın Kalbi) ---
def calculate_precision_metrics(df):
    if len(df) < 20: return None
    data = df.tail(20).copy()
    y = data['Close'].values
    x = np.arange(len(y))
    
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    direction = abs(y[-1] - y[0])
    volatility = np.sum(np.abs(np.diff(y)))
    er = direction / volatility if volatility != 0 else 0
    
    return slope, r_squared, er

def toplu_tarama(ticker_list):
    results = []
    try:
        data = yf.download(ticker_list, period="1y", progress=False)
        if data.empty: return []
        
        closes = data['Close']
        if isinstance(closes, pd.Series): 
            closes = pd.DataFrame({ticker_list[0]: closes})
            
        for ticker in ticker_list:
            try:
                if ticker not in closes: continue
                
                df = pd.DataFrame({'Close': closes[ticker]}).dropna()
                if len(df) < 200: continue 
                
                curr = df['Close'].iloc[-1]
                sma50 = df['Close'].rolling(50).mean().iloc[-1]
                sma200 = df['Close'].rolling(200).mean().iloc[-1]
                
                res = calculate_precision_metrics(df)
                if not res: continue
                slope, r2, er = res
                
                # Torpil bitti! Gerçek formül burada.
                gercek_puan = (r2 * 60) + (er * 40)
                gunluk_hiz = slope if slope > 0.01 else 0.01 
                
                # ⚓ Amiral Masası: 200 Günlük Ortalamanın üstü (Büyük Trend)
                if curr > sma200 and sma50 > sma200:
                    hedef = curr * 1.25
                    tahmini_gun = int((hedef - curr) / gunluk_hiz)
                    results.append({
                        "ticker": ticker, "price": curr, "type": "⚓ AMİRAL", 
                        "target": hedef, "stop": curr*0.90, "r2": r2, "puan": gercek_puan,
                        "vade": tahmini_gun
                    })
                
                # 🛡️ Güven Masası: Doğrusallık (R2 > 0.50)
                elif slope > 0 and r2 > 0.50 and curr > sma50:
                    hedef = curr * 1.10
                    tahmini_gun = int((hedef - curr) / gunluk_hiz)
                    results.append({
                        "ticker": ticker, "price": curr, "type": "🛡️ GÜVEN", 
                        "target": hedef, "stop": curr*0.95, "r2": r2, "puan": gercek_puan,
                        "vade": tahmini_gun
                    })
            except:
                continue
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        
    return results

# --- 7. ARAYÜZ ---
st.sidebar.title(f"Operatör: {st.session_state['current_user'].upper()}")
if st.sidebar.button("🚪 Çıkış Yap"):
    st.session_state['logged_in'] = False
    st.rerun()

tab1, tab2 = st.tabs(["🚀 RADAR (Piyasa Taraması)", "💼 KASA VE PORTFÖY"])

with tab1:
    if st.button("Piyasayı Tara", type="primary", use_container_width=True):
        with st.spinner("Radar dönüyor... Bütün piyasa tek seferde çekiliyor (Ban Korumalı)..."):
            st.session_state['last_results'] = toplu_tarama(WATCHLIST)
            st.session_state['last_results'] = sorted(st.session_state['last_results'], key=lambda x: x['puan'], reverse=True)
        st.success(f"Tarama Tamamlandı. Zayıf hisseler elendi. Kalan: {len(st.session_state['last_results'])} hisse.")

    if st.session_state['last_results']:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="header-box guven-h">🛡️ GÜVEN MASASI (İstikrarlı Kale)</div>', unsafe_allow_html=True)
            for r in [x for x in st.session_state['last_results'] if x['type'] == "🛡️ GÜVEN"][:10]:
                with st.container(border=True):
                    st.markdown(f"<div style='font-size:18px; font-weight:bold;'>{r['ticker']} <span style='float:right;'>${r['price']:.2f}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-row'><span class='data-label'>Algoritma Puanı</span><span class='data-val'>{r['puan']:.0f}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-row'><span class='data-label'>Hedef / Stop</span><span class='data-val'>${r['target']:.2f} / ${r['stop']:.2f}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-row'><span class='data-label'>R² (Doğrusallık)</span><span class='data-val'>{r['r2']:.2f}</span></div>", unsafe_allow_html=True)
                    
                    renk = "green" if r['vade'] < 30 else "orange" if r['vade'] < 90 else "red"
                    st.markdown(f"<div class='data-row'><span class='data-label'>⏳ Tahmini Vade</span><span class='data-val' style='color:{renk};'>Yaklaşık {r['vade']} Gün</span></div>", unsafe_allow_html=True)
                    
        with c2:
            st.markdown('<div class="header-box amiral-h">⚓ AMİRAL MASASI (Büyük Trend)</div>', unsafe_allow_html=True)
            for r in [x for x in st.session_state['last_results'] if x['type'] == "⚓ AMİRAL"][:10]:
                with st.container(border=True):
                    st.markdown(f"<div style='font-size:18px; font-weight:bold; color:#f28b82;'>{r['ticker']} <span style='float:right;'>${r['price']:.2f}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-row'><span class='data-label'>Algoritma Puanı</span><span class='data-val'>{r['puan']:.0f}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-row'><span class='data-label'>Hedef / Stop</span><span class='data-val'>${r['target']:.2f} / ${r['stop']:.2f}</span></div>", unsafe_allow_html=True)
                    
                    renk = "green" if r['vade'] < 60 else "orange" if r['vade'] < 120 else "red"
                    st.markdown(f"<div class='data-row'><span class='data-label'>⏳ Tahmini Vade</span><span class='data-val' style='color:{renk};'>Yaklaşık {r['vade']} Gün</span></div>", unsafe_allow_html=True)

with tab2:
    st.subheader("Operasyon Merkezi (Parça Hisse Destekli)")
    with st.container(border=True):
        secilen = st.selectbox("Hisse Seç", [""] + WATCHLIST)
        meblah = st.number_input("Yatırılacak Tutar ($)", min_value=1.0, value=100.0)
        
        if secilen:
            try:
                curr_p = yf.Ticker(secilen).fast_info['last_price']
                hesaplanan_lot = meblah / curr_p
                st.write(f"Anlık Fiyat: **${curr_p:.2f}** | Alınacak Lot: **{hesaplanan_lot:.4f}**")
                
                if st.button("İşlemi Kaydet (JSON)", type="primary"):
                    new_trade = {
                        "id": int(datetime.now().timestamp()),
                        "sembol": secilen, 
                        "maliyet": round(curr_p, 2), 
                        "tutar": round(meblah, 2), 
                        "lot": round(hesaplanan_lot, 4),
                        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state['portfolio'].append(new_trade)
                    save_portfolio(st.session_state['current_user'], st.session_state['portfolio'])
                    st.success("Tebrikler! İşlem JSON kasasına güvenle kaydedildi.")
                    st.rerun()
            except Exception as e:
                st.error("Canlı fiyat çekilemedi. Bağlantınızı kontrol edin.")

    if st.session_state['portfolio']:
        st.markdown("### Aktif Pozisyonlar")
        df_p = pd.DataFrame(st.session_state['portfolio'])
        st.dataframe(df_p[["tarih", "sembol", "tutar", "lot", "maliyet"]], use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Son Kaydı Sil (Hatalı İşlemi İptal Et)"):
            st.session_state['portfolio'].pop()
            save_portfolio(st.session_state['current_user'], st.session_state['portfolio'])
            st.rerun()