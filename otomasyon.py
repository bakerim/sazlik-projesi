import time
from datetime import datetime
import news_bot  # Senin news_bot.py dosyan
import analysis_engine  # Senin analysis_engine.py dosyan

# --- AYARLAR ---
CALISMA_SIKLIGI_DK = 120  # Kaç dakikada bir tarama yapsın? (Örn: 60 dk)

def sistemi_calistir():
    print("\n" + "="*40)
    print(f"🚀 OTOMASYON BAŞLATILIYOR | {datetime.now().strftime('%d-%m-%Y %H:%M')}")
    print("="*40 + "\n")

    # 1. ADIM: Haberleri Tara (Son 30 Gün)
    print("📰 Adım 1: Haber Botu Sahneye Çıkıyor...")
    try:
        # news_bot içindeki ana fonksiyonu çağırıyoruz
        news_bot.fetch_sweet_spots() 
        print("✅ Haber taraması tamamlandı.\n")
    except Exception as e:
        print(f"❌ Haber Botu Hatası: {e}\n")

    # 2. ADIM: Teknik Analizi Yap
    print("🧠 Adım 2: Analiz Motoru Çalışıyor...")
    try:
        # analysis_engine içindeki ana fonksiyonu çağırıyoruz
        analysis_engine.main_analysis()
        print("✅ Analiz ve Puanlama tamamlandı.\n")
    except Exception as e:
        print(f"❌ Analiz Motoru Hatası: {e}\n")

    print(f"💤 Sistem {CALISMA_SIKLIGI_DK} dakika uyku moduna geçiyor...")
    print("="*40)

# --- SONSUZ DÖNGÜ ---
if __name__ == "__main__":
    while True:
        sistemi_calistir()
        
        # Belirtilen dakika kadar bekle (Saniye cinsinden)
        time.sleep(CALISMA_SIKLIGI_DK * 60)