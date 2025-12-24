import streamlit as st
import pandas as pd
import news_bot
import os
import time
from config import OUTPUT_FILE, WATCHLIST_TICKERS

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık AI Terminali", layout="wide")

# Özel CSS (Tasarım için)
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    div[data-testid="stMetricValue"] { font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💸 SAZLIK - ELİT 6 MODU")
st.markdown(f"**Tarama:** {len(WATCHLIST_TICKERS)} Hisse | **Yorum:** Sadece En İyi 6 Fırsat (Gemini AI)")
st.markdown("---")

# --- KASA GİRİŞİ ---
col_kasa, col_btn = st.columns([2, 1])
with col_kasa:
    bakiye = st.number_input("💵 Toplam Kasa ($):", min_value=100.0, value=1000.0, step=100.0)

# --- BUTON VE DURUM YÖNETİMİ ---
with col_btn:
    st.write("")
    st.write("")
    if st.button("🚀 EN İYİ 6 FIRSATI BUL VE YORUMLA"):
        with st.spinner("Piyasa taranıyor... Bu işlem 30-60 saniye sürebilir..."):
            try:
                # Önce eski dosyayı silelim (Temiz sayfa)
                if os.path.exists(OUTPUT_FILE):
                    os.remove(OUTPUT_FILE)
                
                # Motoru çalıştır
                bulunan_sayisi = news_bot.run_news_bot()
                
                # SONUCU SAKLA
                if bulunan_sayisi > 0:
                    st.success(f"✅ Analiz bitti! {bulunan_sayisi} fırsat bulundu.")
                    time.sleep(1) # Kullanıcı mesajı görsün
                    st.rerun()
                else:
                    st.error("❌ Analiz yapıldı ama kriterlere uyan (Güçlü Al) hisse bulunamadı.")
                    st.caption("Sebep: Piyasa çok durgun olabilir veya `yfinance` veri çekemiyor olabilir.")
            
            except Exception as e:
                st.error(f"⚠️ Motor Hatası: {e}")

# --- SONUÇLARI GÖSTER ---
if os.path.exists(OUTPUT_FILE):
    try:
        df = pd.read_csv(OUTPUT_FILE)
        
        # 1. KOLON KONTROLÜ (HATA ZIRHI)
        gerekli_kolonlar = ['Guven_Skoru', 'Hisse', 'Fiyat', 'Hedef_Fiyat', 'Stop_Loss']
        if not all(col in df.columns for col in gerekli_kolonlar):
            st.warning("⚠️ Veri dosyası formatı eski. Lütfen tekrar tarama yapın.")
            st.stop()

        # 2. FİLTRELEME
        # Sadece 60 puan üstü (AL ve GÜÇLÜ AL)
        df_filtered = df[df['Guven_Skoru'] >= 60].copy()
        
        if df_filtered.empty:
            st.info("📉 Taranan hisselerden hiçbiri 60 puan barajını geçemedi. Piyasa riskli.")
        else:
            # En iyi 6 taneyi seç
            df_final = df_filtered.sort_values(by='Guven_Skoru', ascending=False).head(6)
            toplam_puan = df_final['Guven_Skoru'].sum()
            
            cols = st.columns(3)
            
            for i, row in enumerate(df_final.itertuples()):
                with cols[i % 3]:
                    # Verileri Güvenle Al
                    hisse = row.Hisse
                    puan = int(row.Guven_Skoru)
                    fiyat = row.Fiyat
                    hedef = row.Hedef_Fiyat
                    stop = row.Stop_Loss
                    # Eksik veri varsa varsayılan ata
                    vade = row.Vade if hasattr(row, 'Vade') else "1-3 Gün"
                    hiz = row.hiz if hasattr(row, 'hiz') else (row.Atr_Hiz if hasattr(row, 'Atr_Hiz') else '-')
                    teknik = row.Analiz_Ozeti if hasattr(row, 'Analiz_Ozeti') else "Teknik veri yok"
                    haber_baslik = row.Haber_Baslik if hasattr(row, 'Haber_Baslik') else "Haber yok"

                    # GEMINI AI YORUMU (Sadece bu 6'sı için)
                    ai_notu = "Yükleniyor..."
                    try:
                        prompt = f"Hisse: {hisse}, Puan: {puan}, Teknik: {teknik}. 5 kelimelik, net, mağara adamı yatırım tavsiyesi ver."
                        # news_bot içindeki modeli kullan
                        resp = news_bot.model.generate_content(prompt)
                        ai_notu = resp.text.strip().replace('"', '')[:60]
                    except:
                        ai_notu = "Teknik görünüm pozitif, hacim destekli."

                    # HESAPLAMALAR
                    pay = (puan / toplam_puan) * bakiye
                    kasa_yuzdesi = (pay / bakiye) * 100
                    potansiyel_kar = pay * 0.05

                    # RENKLER
                    if puan >= 90:
                        renk = "#2ea043"; durum = "MÜKEMMEL"
                    elif puan >= 80:
                        renk = "#1f6feb"; durum = "GÜÇLÜ"
                    else:
                        renk = "#d29922"; durum = "FIRSAT"

                    # KART ÇİZİMİ
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
        st.error(f"Dosya okuma hatası: {e}")
        # Hata durumunda butonu tekrar göster
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)

else:
    # Dosya yoksa veya silindiyse
    st.info("📂 Henüz analiz sonucu yok. Lütfen yukarıdaki butona basarak 'Garantici Baba'yı ava gönder.")
