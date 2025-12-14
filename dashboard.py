import streamlit as st
import pandas as pd
import altair as alt
import yfinance as yf
import pandas_ta as ta

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Sazlık Pro - Komuta Merkezi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS TASARIMI (Görsel Motor) ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    
    /* TAB 3: OPERASYON KARTI (ELITE DESIGN) */
    .op-card {
        background: #161b22;
        border: 2px solid #238636; /* Neon Yeşil Çerçeve */
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 0 25px rgba(35, 134, 54, 0.15);
    }
    .op-header {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #30363d; padding-bottom: 15px; margin-bottom: 20px;
    }
    .op-title { font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: 1px; }
    .op-badge { 
        background-color: #238636; color: white; padding: 5px 15px; 
        border-radius: 20px; font-size: 14px; font-weight: bold;
    }
    
    /* YOL HARİTASI (ROADMAP) */
    .roadmap-container {
        display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px;
    }
    .roadmap-step {
        background: rgba(255, 255, 255, 0.05); border: 1px solid #30363d; border-radius: 8px; padding: 15px;
        text-align: center;
    }
    .step-title { color: #8b949e; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .step-price { color: #3fb950; font-size: 20px; font-weight: bold; margin-bottom: 5px; }
    .step-desc { color: #e6edf3; font-size: 13px; line-height: 1.4; }
    .step-time { color: #58a6ff; font-size: 11px; font-style: italic; margin-top: 5px; }

    /* DİĞER STİLLER (Eski kodlardan korunanlar) */
    .top-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px; }
    .info-box { padding: 15px; border-radius: 10px; text-align: center; color: white; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1); }
    .detective-card { background-color: #161b22; border: 2px solid #58a6ff; border-radius: 15px; padding: 30px; text-align: center; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
    .text-green { color: #3fb950 !important; } .text-red { color: #f85149 !important; }
</style>
""", unsafe_allow_html=True)

# --- İZLEME LİSTESİ ---
FULL_WATCHLIST = [
    "NVDA", "META", "TSLA", "AVGO", "AMZN", "MSFT", "GOOGL", "PLTR", "MSTR", "COIN"
]

# --- VERİ YÜKLEME ---
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv("sazlik_signals.csv", on_bad_lines='skip', engine='python')
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        required = ['Hisse', 'Fiyat', 'Karar', 'Guven_Skoru', 'Hedef_Fiyat', 'Stop_Loss', 'Vade', 'Analiz_Ozeti', 'Kazanc_Potansiyeli', 'Risk_Yuzdesi']
        for col in required:
            if col not in df.columns: df[col] = "-"
        df = df.sort_values('Tarih', ascending=False).drop_duplicates('Hisse')
        df['Guven_Skoru_Num'] = pd.to_numeric(df['Guven_Skoru'], errors='coerce').fillna(0)
        return df[df['Hisse'].isin(FULL_WATCHLIST)]
    except:
        return pd.DataFrame()

df = pd.DataFrame()
df = load_data()

def safe_val(val, prefix=""):
    try:
        if pd.isna(val) or str(val).lower() in ['nan', '0', '']: return '-'
        return f"{prefix}{val}"
    except: return '-'

# --- SNIPER ANALİZİ ---
def analyze_sniper(ticker):
    try:
        df_sniper = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df_sniper.columns, pd.MultiIndex):
            df_sniper.columns = df_sniper.columns.get_level_values(0)
        
        if len(df_sniper) < 200: return None
        
        df_sniper.ta.rsi(length=14, append=True)
        df_sniper.ta.sma(length=20, append=True)
        df_sniper.ta.sma(length=50, append=True)
        df_sniper.ta.sma(length=200, append=True)
        
        last_row = df_sniper.iloc[-1]
        close = last_row['Close']
        sma20 = last_row['SMA_20']
        sma50 = last_row['SMA_50']
        sma200 = last_row['SMA_200']
        rsi = last_row['RSI_14']
        
        durum = "BEKLE"
        if (close > sma200 and close > sma50) and (rsi >= 55) and (close > sma20):
            durum = "AL (SNIPER)"
        elif close < sma50: 
            durum = "SAT"
        
        return { "Hisse": ticker, "Fiyat": close, "RSI": rsi, "Durum": durum }
    except: return None

# --- CANLI ANALİZ ---
def canli_analiz_yap(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if len(hist) < 200: return None
        curr_price = hist['Close'].iloc[-1]
        hist.ta.rsi(length=14, append=True)
        score = 50
        rsi = hist['RSI_14'].iloc[-1]
        if rsi < 30: score += 25
        elif rsi < 40: score += 10
        elif rsi > 70: score -= 20
        karar = "BEKLE"
        if score >= 60: karar = "AL"
        elif score <= 30: karar = "SAT"
        return {
            'Hisse': ticker, 'Fiyat': curr_price, 'Karar': karar, 'Guven_Skoru_Num': score,
            'Hedef_Fiyat': curr_price * 1.05, 'Stop_Loss': curr_price * 0.95,
            'Vade': "1-2 Hafta", 'Analiz_Ozeti': f"RSI: {rsi:.1f}"
        }
    except: return None

# --- 4. ANA EKRAN ---
st.title("🌾 Sazlık Pro: Komuta Merkezi")
st.markdown(f"**Aktif Özel Tim:** `{', '.join(FULL_WATCHLIST)}`")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 AI Vitrini", "📊 Portföy Analizi", "🧪 250$ Deney Labı", "🗃️ Veri Havuzu", "🔎 Hisse Dedektifi"
])

# --- TAB 1 & 2: STANDART ---
with tab1:
    st.info("AI Vitrini verileri güncelleniyor...")
with tab2:
    st.info("Portföy analizleri güncelleniyor...")

# ==============================================================================
# --- TAB 3: SNIPER ELITE LABORATUVARI (V20.0) ---
# ==============================================================================
with tab3:
    st.markdown("## 🧪 250$ Deney Laboratuvarı: SNIPER ELITE")
    st.markdown("Bu panel, backtest verilerine dayalı **3 Kademeli Kar Alma (Scale-Out)** stratejisini uygular.")
    
    col_in, col_inf = st.columns([1, 2])
    budget = col_in.number_input("Kasa ($)", value=250.0, step=10.0)
    trade_budget = budget * 0.98
    col_inf.success(f"**Savaş Bütçesi:** ${trade_budget:.2f} (Komisyon düşüldü, Parça Hisse Alımı Aktif)")

    if st.button("🚀 Piyasayı Tara ve Yol Haritasını Çıkar", type="primary"):
        with st.spinner("Strateji hesaplanıyor... Hedefler belirleniyor..."):
            opportunities = []
            for ticker in FULL_WATCHLIST:
                res = analyze_sniper(ticker)
                if res and res["Durum"] == "AL (SNIPER)":
                    opportunities.append(res)
            
            opportunities.sort(key=lambda x: x["RSI"], reverse=True)
            
            if not opportunities:
                st.warning("### 💤 Pusuya Devam")
                st.write("Şu an atış menzilinde uygun hisse yok.")
            else:
                plan_a = opportunities[0]
                plan_b = opportunities[1] if len(opportunities) > 1 else None
                
                # --- OPERASYON KARTI FONKSİYONU ---
                def render_roadmap_card(plan, label):
                    ticker = plan['Hisse']
                    entry_price = plan['Fiyat']
                    rsi = plan['RSI']
                    
                    # HEDEFLER (BACKTEST VERİLERİNE DAYALI)
                    target_1 = entry_price * 1.10  # %10
                    target_2 = entry_price * 1.30  # %30
                    target_3 = entry_price * 1.50  # %50+
                    stop_loss = entry_price * 0.92 # %8
                    
                    # GETİRİ HESABI
                    # Senaryo: %50'si ilk hedefte, %25'i ikinci hedefte, %25'i üçüncü hedefte satılırsa
                    total_shares_val = trade_budget
                    profit_1 = (total_shares_val * 0.50) * 0.10
                    profit_2 = (total_shares_val * 0.25) * 0.30
                    profit_3 = (total_shares_val * 0.25) * 0.50
                    total_potential_profit = profit_1 + profit_2 + profit_3
                    
                    html = f"""
                    <div class="op-card">
                        <div class="op-header">
                            <div class="op-title">{label}: {ticker}</div>
                            <div class="op-badge">RSI GÜCÜ: {rsi:.1f}</div>
                        </div>
                        
                        <div style="display:flex; justify-content:space-between; margin-bottom:15px; border-bottom:1px solid #30363d; padding-bottom:15px;">
                            <div>
                                <div class="op-label">GİRİŞ FİYATI</div>
                                <div class="op-value">${entry_price:.2f}</div>
                            </div>
                            <div style="text-align:right;">
                                <div class="op-label">YATIRILACAK</div>
                                <div class="op-value text-green">${trade_budget:.2f}</div>
                            </div>
                        </div>
                        
                        <div style="margin-bottom:20px;">
                            <div class="op-label">📄 GÖREV EMRİ</div>
                            <div style="color:#e6edf3; font-size:15px; margin-top:5px;">
                                <b>Parça Hisse (Fractional)</b> emri ile <b>${trade_budget:.2f}</b> tutarında {ticker} al.
                                <br><span style="color:#f85149; font-size:13px;">(Stop Loss: ${stop_loss:.2f})</span>
                            </div>
                        </div>
                        
                        <div class="op-label" style="text-align:center; margin-bottom:10px;">📍 3 KADEMELİ SATIŞ ROTASI</div>
                        
                        <div class="roadmap-container">
                            <div class="roadmap-step">
                                <div class="step-title">1. GÜVENLİK KİLİDİ</div>
                                <div class="step-price">${target_1:.2f}</div>
                                <div class="step-desc">Elindekinin <b>%50'sini</b> sat.<br><span style="color:#3fb950">Kazanç: +${profit_1:.2f}</span></div>
                                <div class="step-time">Tahmini: 1-3 Hafta</div>
                            </div>
                            
                            <div class="roadmap-step">
                                <div class="step-title">2. TREND KAZANCI</div>
                                <div class="step-price">${target_2:.2f}</div>
                                <div class="step-desc">Elindekinin <b>%25'ini</b> sat.<br><span style="color:#3fb950">Kazanç: +${profit_2:.2f}</span></div>
                                <div class="step-time">Tahmini: 1-2 Ay</div>
                            </div>
                            
                            <div class="roadmap-step">
                                <div class="step-title">3. JACKPOT</div>
                                <div class="step-price">${target_3:.2f}+</div>
                                <div class="step-desc">Kalan <b>%25'i</b> Trailing Stop ile sür.<br><span style="color:#3fb950">Kazanç: +${profit_3:.2f}+</span></div>
                                <div class="step-time">Tahmini: 3-6 Ay</div>
                            </div>
                        </div>
                        
                        <div style="margin-top:20px; text-align:center; font-size:14px; color:#8b949e;">
                            🎯 Operasyon Başarılı Olursa Toplam Tahmini Kar: <b style="color:#3fb950">${total_potential_profit:.2f}</b>
                        </div>
                    </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)

                st.markdown(f"### 🔥 TESPİT EDİLEN FIRSATLAR ({len(opportunities)} Adet)")
                render_roadmap_card(plan_a, "PLAN A")
                
                if plan_b:
                    st.markdown("👇 **Alternatif:**")
                    render_roadmap_card(plan_b, "PLAN B")

# --- TAB 4: VERİ ---
with tab4:
    st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True)

# --- TAB 5: DEDEKTİF ---
with tab5:
    st.header("🔎 Hisse Dedektifi")
    sel = st.selectbox("Hisse Seç:", sorted(FULL_WATCHLIST))
    if st.button("Analiz Et"):
        with st.spinner("Bakılıyor..."):
            r = canli_analiz_yap(sel)
            if r:
                c1, c2 = st.columns(2)
                with c1:
                    score = int(r['Guven_Skoru_Num'])
                    clr = "#238636" if score >= 70 else "#da3633"
                    st.markdown(f"""<div class="detective-card"><h1 style='color:white'>{r['Hisse']}</h1><h2 style='color:{clr}; font-size:48px'>{score}</h2><p style='color:#888'>PUAN</p></div>""", unsafe_allow_html=True)
                with c2:
                    st.metric("Fiyat", f"${r['Fiyat']:.2f}")
                    st.metric("Hedef", f"${r['Hedef_Fiyat']:.2f}")
                    st.info(r['Analiz_Ozeti'])
            else: st.error("Hata.")
