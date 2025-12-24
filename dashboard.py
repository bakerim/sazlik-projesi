import streamlit as st
import pandas as pd
import news_bot  # Garantici Baba motoru
import os
from config import OUTPUT_FILE, WATCHLIST_TICKERS

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sazlık AI Terminali", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    stCodeBlock { background-color: #161b22 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("💸 SAZLIK - ELİT 6 MODU")
st.markdown(f"**Tarama:** {len(WATCHLIST_TICKERS)} Hisse | **Yorum:** Sadece En İyi 6 Fırsat (Gemini AI)")
st.markdown("---")

# --- KASA GİRİŞİ ---
col_kasa, col_btn = st.columns([2, 1])
with col_kasa:
    bakiye = st.number_input("💵 Toplam Kasa ($):", min_value=100.0, value=1000.0, step=100.0)

with col_btn:
    st.write("")
    st.write("")
    if st.button("🚀 EN İYİ 6 FIRSATI BUL VE YORUMLA"):
        with st.spinner("Piyasa taranıyor... Eski veriler temizleniyor..."):
            try:
                # Önce eski dosyayı silelim ki temiz başlangıç olsun
                if os.path.exists(OUTPUT_FILE):
                    os.remove(OUTPUT_FILE)
                
                # Motoru çalıştır
                sayi = news_bot.run_news_bot()
                st.success(f"Analiz tamamlandı! {sayi} hisse tarandı.")
                st.rerun() # Sayfayı yenile
            except Exception as e:
                st.error(f"Motor Hatası: {e}")

# --- SONUÇLARI GÖSTER ---
if os.path.exists(OUTPUT_FILE):
    try:
        df = pd.read_csv(OUTPUT_FILE)
        
        # SÜTUN KONTROLÜ (HATA BURADAYDI)
        if 'Guven_Skoru' not in df.columns:
            st.error("⚠️ Eski veri dosyası tespit edildi. Lütfen yukarıdaki butona basarak yeniden tarama yapın.")
            os.remove(OUTPUT_FILE) # Bozuk dosyayı sil
            st.stop()

        # Güçlü Sinyalleri Al
        df = df[df['Guven_Skoru'] >= 60]
        df = df.sort_values(by='Guven_Skoru', ascending=False).head(6)
        
        if df.empty:
            st.info("📉 Kriterlere uygun (60+) hisse bulunamadı. Piyasa bugün zayıf olabilir.")
        else:
            toplam_puan = df['Guven_Skoru'].sum()
            cols = st.columns(3)
            
            for i, row in enumerate(df.itertuples()):
                with cols[i % 3]:
                    # 1. TEMEL VERİLER
                    hisse = row.Hisse
                    puan = int(row.Guven_Skoru)
                    teknik_yorum = row.Analiz_Ozeti
                    haber_baslik = row.Haber_Baslik if hasattr(row, 'Haber_Baslik') else "Haber yok"
                    
                    # 2. HIZ (ATR) VERİSİ
                    hiz_veri = row.hiz if hasattr(row, 'hiz') else (row.Atr_Hiz if hasattr(row, 'Atr_Hiz') else '-')

                    # 3. GEMINI AI YORUMU
                    with st.spinner(f"AI {hisse} yorumluyor..."):
                        try:
                            prompt = (f"Sen agresif bir borsa yatırımcısısın. Hisse: {hisse}, Puan: {puan}, "
                                      f"Teknik: {teknik_yorum}, Haber: {haber_baslik}. "
                                      f"Bana 5 kelimelik, net, emredici bir yatırım tavsiyesi ver.")
                            response = news_bot.model.generate_content(prompt)
                            ai_notu = response.text.strip().replace('"', '')[:75]
                        except:
                            ai_notu = "Teknik görünüm sağlam, hacim artışıyla pozisyon alınabilir."

                    # 4. KASA VE RENK HESABI
                    pay = (puan / toplam_puan) * bakiye
                    kasa_yuzdesi = (pay / bakiye) * 100
                    potansiyel_kar = pay * 0.05
                    
                    if puan >= 90:
                        renk = "#2ea043" # Yeşil
                        durum = "MÜKEMMEL"
                    elif puan >= 80:
                        renk = "#1f6feb" # Mavi
                        durum = "GÜÇLÜ"
                    else:
                        renk = "#d29922" # Turuncu
                        durum = "FIRSAT"

                    # 5. KART ÇİZİMİ
                    st.markdown(f"""
                    <div style="border: 2px solid {renk}; border-radius: 12px; padding: 15px; margin-bottom: 10px; background-color: rgba(255,255,255,0.03);">
                        <h2 style="color: {renk}; margin: 0; text-align: center; font-size: 30px;">{hisse}</h2>
                        <p style="color: white; text-align: center; margin: 0; font-weight: bold;">{durum} (SKOR: {puan})</p>
                        <hr style="border-color: {renk}; opacity: 0.2; margin: 10px 0;">
                        <p style="color: #00ff00; font-size: 13px; margin: 0 0 5px 0;"><b>🧠 AI NOTU:</b> <span style="color: #ccc;">{ai_notu}</span></p>
                        <p style="color: #4ea8de; font-size: 11px; margin: 0;"><b>📊 TEKNİK:</b> {teknik_yorum[:80]}...</p>
                        <div style="margin-top: 10px; padding: 5px; border-radius: 4px; background: rgba(0,0,0,0.2);">
                            <p style="color: #eee; font-size: 10px; margin:0;">📢 {haber_baslik[:60]}...</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.code(f"""
💰 YATIRIM: ${pay:.2f} (Kasanın %{kasa_yuzdesi:.1f}'i)
💵 POT. KÂR: +${potansiyel_kar:.2f}

👉 EMİR: AL
📉 GİRİŞ:   ${row.Fiyat}
🎯 HEDEF:   ${row.Hedef_Fiyat}
🛑 STOP:    ${row.Stop_Loss}
⏳ VADE:    {row.Vade}
⚡ HIZ:     %{hiz_veri} / gün
                    """, language="yaml")

    except Exception as e:
        # Eğer okurken hata verirse dosyayı sil ve uyar
        st.error(f"Dosya okuma hatası: {e}")
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
            st.warning("Bozuk veri dosyası silindi. Lütfen tekrar tarama yapın.")

else:
    st.info("📂 Henüz analiz yapılmamış. Butona basarak 'Garantici Baba'yı ava gönder.")
