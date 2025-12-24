import streamlit as st
import pandas as pd
import news_bot  # Senin Garantici Baba motorun
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
        with st.spinner("Piyasa taranıyor... Sadece en iyiler AI süzgecine alınıyor..."):
            try:
                sayi = news_bot.run_news_bot()
                st.success(f"Analiz tamamlandı. Veriler güncellendi!")
            except Exception as e:
                st.error(f"Hata: {e}")

# --- SADECE SEÇİLEN 6 HİSSEYİ GÖSTER ---
if os.path.exists(OUTPUT_FILE):
    df = pd.read_csv(OUTPUT_FILE)
    
    # Güçlü Sinyalleri Al ve En Yüksek 6 Taneye Odaklan
    df = df[df['Guven_Skoru'] >= 60]
    df = df.sort_values(by='Guven_Skoru', ascending=False).head(6)
    
    if df.empty:
        st.info("📉 Kriterlere uygun (60+) hisse bulunamadı. Lütfen taramayı başlat.")
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
                
                # 2. SADECE BU 6 HİSSE İÇİN GEMINI'DEN YORUM AL
                # (Hız ve maliyet tasarrufu için sadece ekrana basılanlara soruyoruz)
                with st.spinner(f"AI {hisse} analizini yapıyor..."):
                    try:
                        prompt = (f"Sen bir hedge fon yöneticisisin. Hisse: {hisse}, Puan: {puan}, "
                                  f"Teknik: {teknik_yorum}, Haber: {haber_baslik}. "
                                  f"Bu verileri 5-7 kelimelik, net, emredici bir 'Mağara Adamı' yatırımcı notu olarak yaz.")
                        response = news_bot.model.generate_content(prompt)
                        ai_notu = response.text.strip().replace('"', '')[:75]
                    except:
                        ai_notu = "Teknik görünüm sağlam, hacim artışıyla pozisyon alınabilir."

                # 3. KASA VE RENK HESABI
                pay = (puan / toplam_puan) * bakiye
                if puan >= 90:
                    renk = "#2ea043" # Yeşil
                    durum = "MÜKEMMEL"
                elif puan >= 80:
                    renk = "#1f6feb" # Mavi
                    durum = "GÜÇLÜ"
                else:
                    renk = "#d29922" # Turuncu
                    durum = "FIRSAT"

                # 4. KART ÇİZİMİ
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
💰 YATIRIM: ${pay:.2f}
📉 GİRİŞ:   ${row.Fiyat}
🎯 HEDEF:   ${row.Hedef_Fiyat}
🛑 STOP:    ${row.Stop_Loss}
⏳ VADE:    {row.Vade}
                """, language="yaml")
else:
    st.info("📂 Henüz analiz yapılmamış. Butona basarak 'Garantici Baba'yı ava gönder.")
