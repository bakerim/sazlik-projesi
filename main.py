from sazlik_motoru import SazlikAnaliz
import pandas as pd

def rapor_olustur():
    # 1. Motoru Başlat
    motor = SazlikAnaliz()
    
    # 2. Analizi Yap
    print("Analizler yapılıyor, grafikler çiziliyor...")
    df = motor.analiz_et()
    
    # 3. Sonuçları Excel'e Kaydet
    dosya_adi = "Sazlik_Gunluk_Rapor.xlsx"
    
    # Excel yazıcısı (Renklendirme için)
    # Eğer openpyxl hatası alırsan: pip install openpyxl
    try:
        df.to_excel(dosya_adi, index=False)
        print(f"\n✅ Rapor başarıyla oluşturuldu: {dosya_adi}")
        print("📂 Kritik sinyaller 'raporlar' klasörüne grafik olarak kaydedildi.")
        
        # Konsola Özet Geç
        print("\n--- DİKKAT ÇEKENLER ---")
        dikkat = df[df['Aksiyon'] != "YOK"]
        if not dikkat.empty:
            print(dikkat[['Hisse', 'Fiyat', 'Sinyal', 'Aksiyon']])
        else:
            print("Bugün için yeni bir AL/SAT sinyali yok. Mevcut pozisyonlar korunuyor.")
            
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    rapor_olustur()