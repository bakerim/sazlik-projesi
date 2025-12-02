import streamlit as st
import google.generativeai as genai
import feedparser
import json
import time
import yfinance as yf  # <--- YENİ KÜTÜPHANE

# ... (Ayarlar ve CSS kısımları aynı kalacak) ...

# --- YARDIMCI FONKSİYON: FİYAT KONTROLÜ ---
def get_price_data(ticker):
    """
    Hissenin anlık fiyat değişimini kontrol eder.
    Eğer hisse çoktan uçmuşsa bizi uyarır.
    """
    try:
        # BIST hissesi mi Global mi anlamaya çalışalım
        # BIST ise sonuna .IS eklemek gerekebilir (Örn: THYAO.IS)
        # AI bazen düz verir, biz garanti olsun diye hem normal hem .IS deneriz.
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        
        if hist.empty:
            # Belki BIST hissesidir, .IS ekleyip deneyelim
            stock = yf.Ticker(f"{ticker}.IS")
            hist = stock.history(period="1d")

        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[0]
            # Yüzdelik değişimi hesapla
            change_percent = ((current_price - open_price) / open_price) * 100
            return change_percent, current_price
        else:
            return None, None
    except:
        return None, None

# ... (Prompt kısmı aynı) ...

def analyze_market():
    # ... (Haber çekme ve AI analiz kısımları aynı) ...
    
    # ... (AI'dan 'signals' listesi geldikten sonra ŞU DÖNGÜYÜ DEĞİŞTİRİYORUZ) ...
        
        if not signals:
            st.info("🤷‍♂️ Fırsat yok...")
        else:
            for s in signals:
                ticker = s.get('Ticker', 'UNKNOWN')
                
                # --- YENİ EKLENEN KISIM: FİYAT KONTROLÜ ---
                real_change, real_price = get_price_data(ticker)
                
                # "Atı Alan Üsküdar'ı Geçti mi?" Kontrolü
                is_late = False
                price_warning = ""
                
                if real_change is not None:
                    # KURAL: Eğer hisse %4'ten fazla artmışsa GEÇ KALDIK demektir.
                    if real_change > 4.0: 
                        is_late = True
                        price_warning = f"⚠️ <b>DİKKAT:</b> Hisse bugün zaten <b>%{real_change:.2f}</b> yükselmiş! Tren kaçmış olabilir, geri çekilme bekle."
                        color_class = "warning" # Rengi sarı/turuncu yap
                    else:
                        price_warning = f"✅ <b>Fiyat Uygun:</b> Günlük değişim sadece %{real_change:.2f}. Henüz patlamamış."
                else:
                    price_warning = "ℹ️ Anlık fiyat verisi çekilemedi (Ticker hatası olabilir)."
                
                # Kart Rengi ve Başlık
                if is_late:
                    card_title = f"🚨 GEÇ KALDIN: {ticker} (Riskli Yükseliş)"
                else:
                    card_title = f"💎 SİNYAL: {ticker} ({s['Action']})"

                html_card = f"""
                <div class="signal-card {color_class}">
                    <h3>{card_title}</h3>
                    <p><b>Güven Puanı:</b> %{s['Confidence']} | <b>Risk:</b> {s['Risk_Level']}</p>
                    <div style="background-color: #444; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        {price_warning}
                    </div>
                    <hr style="border-color: #555;">
                    <p>📝 <b>Neden:</b> {s['Reason']}</p>
                    <p>💰 <b>Kasa Planı:</b> {s['Entry_Plan']}</p>
                    <p>🛑 <b>Stop-Loss:</b> {s['Stop_Loss']} | 🎯 <b>Hedef:</b> {s['Target']}</p>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
