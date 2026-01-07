import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
import sys

# Grafik Stili (Dark Mode - Matrix Havası)
plt.style.use('dark_background')

def infografik_olustur():
    try:
        # 1. Veriyi Oku (Önceki kodun ürettiği CSV)
        df = pd.read_csv('sazlik_islem_gecmisi.csv')
        
        if df.empty:
            print("CSV dosyası boş veya bulunamadı!")
            return

        # Tarih formatını düzelt
        df['Satis_Tarihi'] = pd.to_datetime(df['Satis_Tarihi'])
        df = df.sort_values(by='Satis_Tarihi')

        # Kümülatif Kasa Eğrisi Oluştur
        df['Kasa_Egrio'] = df['Net_PNL'].cumsum() + 10000  # 10k Başlangıç varsayıldı

        # --- TUVALLERİ HAZIRLA ---
        fig = plt.figure(figsize=(20, 12))
        fig.suptitle('SAZLIK PROJESİ - PERFORMANS KARNESİ', fontsize=24, color='#00ff00', fontweight='bold')
        
        # Grid Sistemi (Dashboard Düzeni)
        gs = GridSpec(2, 3, figure=fig)
        
        # 1. GRAFİK: KASA BÜYÜME EĞRİSİ (SOL ÜST - GENİŞ)
        ax1 = fig.add_subplot(gs[0, 0:2])
        ax1.plot(df['Satis_Tarihi'], df['Kasa_Egrio'], color='#00ff00', linewidth=2)
        ax1.fill_between(df['Satis_Tarihi'], df['Kasa_Egrio'], 10000, color='#00ff00', alpha=0.1)
        ax1.set_title('💰 Kasa Büyüme Eğrisi (Equity Curve)', fontsize=14, color='white')
        ax1.grid(True, alpha=0.2)
        
        # 2. GRAFİK: GALİBİYET / MAĞLUBİYET ORANI (SAĞ ÜST)
        ax2 = fig.add_subplot(gs[0, 2])
        win_count = len(df[df['Sonuc'] == 'KAR (TP)'])
        loss_count = len(df[df['Sonuc'] == 'ZARAR (SL)'])
        colors = ['#00ff00', '#ff0000']
        ax2.pie([win_count, loss_count], labels=['KAZANÇ', 'KAYIP'], autopct='%1.1f%%', 
                colors=colors, startangle=90, explode=(0.1, 0), textprops={'color':"white"})
        ax2.set_title('🎯 Başarı Oranı (Win Rate)', fontsize=14)

        # 3. GRAFİK: EN ÇOK KAZANDIRAN 5 HİSSE (SOL ALT)
        ax3 = fig.add_subplot(gs[1, 0])
        top_winners = df.groupby('Sembol')['Net_PNL'].sum().sort_values(ascending=False).head(5)
        sns.barplot(x=top_winners.values, y=top_winners.index, ax=ax3, palette='Greens_r')
        ax3.set_title('👑 Şampiyonlar Ligi (Top 5)', fontsize=14)
        ax3.set_xlabel('Toplam Kar ($)')

        # 4. GRAFİK: EN ÇOK KAYBETTİREN 5 HİSSE (ORTA ALT)
        ax4 = fig.add_subplot(gs[1, 1])
        top_losers = df.groupby('Sembol')['Net_PNL'].sum().sort_values(ascending=True).head(5)
        sns.barplot(x=top_losers.values, y=top_losers.index, ax=ax4, palette='Reds_r')
        ax4.set_title('💀 Kara Liste (Bottom 5)', fontsize=14)
        ax4.set_xlabel('Toplam Zarar ($)')

        # 5. GRAFİK: KAZANÇ DAĞILIMI (SAĞ ALT - HİSTOGRAM)
        ax5 = fig.add_subplot(gs[1, 2])
        sns.histplot(df['Net_PNL'], bins=30, kde=True, color='cyan', ax=ax5)
        ax5.axvline(0, color='white', linestyle='--')
        ax5.set_title('📊 Kar/Zarar Dağılımı', fontsize=14)
        ax5.set_xlabel('İşlem Başına PNL')

        # Görseli Kaydet ve Göster
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig('sazlik_infografik.png', dpi=300)
        print("✅ İnfografik oluşturuldu: 'sazlik_infografik.png'")
        # plt.show() # Eğer masaüstü uygulamasındaysan bunu açabilirsin.

    except FileNotFoundError:
        print("❌ HATA: 'sazlik_islem_gecmisi.csv' dosyası bulunamadı!")
        print("   Önce V4 kodunu çalıştırıp CSV dosyasını oluşturmalısın.")

if __name__ == "__main__":
    infografik_olustur()