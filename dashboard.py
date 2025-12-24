import streamlit as st
import pandas as pd
import news_bot
import os
import time
from config import OUTPUT_FILE, WATCHLIST_TICKERS

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık AI Terminali", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    div[data-testid="stMetricValue"] { font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💸 SAZLIK - DELİKANLI MODU (FULL TARAMA)")
st.markdown(f"**Hedef:** {len(WATCHLIST_TICKERS)} Hisse (Tam Liste) | **Filtre:** Garantici Baba + 20 Gün Sigortası")
st.markdown("---")

# --- KASA GİRİŞİ ---
col_kasa, col_btn = st.columns([2, 1])
with col_kasa:
    bakiye = st.number_input("💵 Toplam Kasa ($):", min_value=100.0, value=1000.0, step=100.0)

# --- BUTON ---
with col_btn:
    st.write("")
    st.write("")
    if st.button("🚀 PİYASANIN İÇİNDEN GEÇ (FULL TARAMA)"):
        # Buradaki yazıyı değiştirdim
        msg = st.empty()
        msg.info("🔥 350+ Hisse tek tek taranıyor... Çayını kahveni al, bu işlem piyasanın durumuna göre 2-3 dakika sürebilir. Sakın kapatma!")
        
        try:
            # Eski dosyayı sil
            if os.path.exists(OUTPUT_FILE):
                os.remove(OUTPUT_FILE)
            
            # Motoru çalıştır
            start_time = time.time()
            bulunan_sayisi = news_bot.run_news_bot()
            end_time = time.time()
            
            sure = int(end_time - start_time)
            
            if bulunan_sayisi > 0:
                msg.success(f"✅ Bitti! {sure} saniyede piyasa tarandı ve {bulunan_sayisi} fırsat bulundu.")
                time.sleep(2)
                st.rerun()
            else:
                msg.error("❌ Koca piyasada kriterlerine uyan tek bir hisse bile çıkmadı. Nakitte kal.")
        
        except Exception as e:
            msg.error(f"⚠️ Hata: {e}")

# --- SONUÇLARI GÖSTER ---
if os.path.exists(OUTPUT_FILE):
    try:
        df = pd.read_csv(OUTPUT_FILE)
        
        # Filtreleme
        df_filtered = df[df['Guven_Skoru'] >= 60].copy()
        
        if df_filtered.empty:
            st.info("📉 Taranan hisseler 60 puanı geçemedi.")
        else:
            # En iyi 6 taneyi seç
            df_final = df_filtered.sort_values(by='Guven_Skoru', ascending=False).head(6)
            toplam_puan = df_final['Guven_Skoru'].sum()
            
            cols = st.columns(3)
            
            for i, row in enumerate(df_final.itertuples()):
                with cols[i % 3]:
                    # Veriler
                    hisse = row.Hisse
                    puan = int(row.Guven_Skoru)
                    fiyat = row.Fiyat
                    hedef = row.Hedef_Fiyat
                    stop = row.Stop_Loss
                    vade = row.Vade if hasattr(row, 'Vade') else "1-3 Gün"
                    hiz = row.hiz if hasattr(row, 'hiz') else '-'
                    teknik = row.Analiz_Ozeti if hasattr(row, 'Analiz_Ozeti') else "Veri yok"
                    haber_baslik = row.Haber_Baslik if hasattr(row, 'Haber_Baslik') else "Haber yok"

                    # GEMINI AI
                    ai_notu = "Yükleniyor..."
                    try:
                        prompt = f"Hisse: {hisse}, Puan: {puan}, Teknik: {teknik}. 5 kelimelik, net, sert bir borsa koçu tavsiyesi ver."
                        resp = news_bot.model.generate_content(prompt)
                        ai_notu = resp.text.strip().replace('"', '')[:60]
                    except:
                        ai_notu = "Teknik onaylı, trend güçlü."

                    # HESAP
                    pay = (puan / toplam_puan) * bakiye
                    kasa_yuzdesi = (pay / bakiye) * 100
                    potansiyel_kar = pay * 0.05

                    # RENK
                    if puan >= 90: renk = "#2ea043"; durum = "MÜKEMMEL"
                    elif puan >= 80: renk = "#1f6feb"; durum = "GÜÇLÜ"
                    else: renk = "#d29922"; durum = "FIRSAT"

                    # KART
                    st.markdown(f"""
                    <div style="border: 2px solid {renk}; border-radius: 12px; padding: 15px; margin-bottom: 10px; background-color: rgba(255,255,255,0.03);">
                        <h2 style="color: {renk}; margin: 0; text-align: center; font-size: 30px;">{hisse}</h2>
                        <p style="color: white; text-align: center; margin: 0; font-weight: bold;">{durum} (SKOR: {puan})</p>
                        <hr style="border-color: {renk}; opacity: 0.2; margin: 10px 0;">
                        <p style="color: #00ff00; font-size: 13px; margin: 0 0 5px 0;"><b>🧠 AI NOTU:</b> <span style="color: #ccc;">{ai_notu}</span></p>
                        <p style="color: #4ea8de; font-size: 11px; margin: 0;"><b>📊 TEKNİK:</b> {str(teknik)[:80]}...</p>
                        <div style="margin-top: 10px; padding: 5px; border-radius: 4px; background: rgba(0,0,0,0.2);">
                            <p style="color: #eee; font-size: 10px; margin:0;">📢 {str(haber_baslik)[:60]}...</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.code(f"""
💰 YATIRIM: ${pay:.2f} (%{kasa_yuzdesi:.1f})
💵 POT. KÂR: +${potansiyel_kar:.2f}

👉 EMİR: AL
📉 GİRİŞ:   ${fiyat}
🎯 HEDEF:   ${hedef}
🛑 STOP:    ${stop}
⏳ VADE:    {vade}
⚡ HIZ:     %{hiz} / gün
                    """, language="yaml")
    except Exception as e:
        if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
        st.error("Dosya okuma hatası, tekrar dene.")
else:
    st.info("📂 Analiz bekleniyor. Butona bas ve yaslan.")
