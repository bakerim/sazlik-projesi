import pandas as pd
import json
import requests
import os
import time
import warnings
from datetime import datetime, timedelta
from colorama import Fore, init
import news_bot  # O gelişmiş beyni buraya çağırıyoruz
from config import OUTPUT_FILE, GITHUB_TOKEN, GIST_ID, WATCHLIST_TICKERS

# Uyarıları kapat
warnings.simplefilter(action='ignore', category=FutureWarning)
init(autoreset=True)

# --- AYARLAR ---
LOCAL_DB = "sazlik_cuzdan.json"
MIN_PUAN_LIMITI = 80  # Sadece 80 ve üzeri puan alanlar
KAR_AL = 0.05  # %5 Kar görünce sat
ZARAR_KES = 0.03 # %3 Zarar görünce sat

class SazlikForwardBot:
    def __init__(self):
        self.db = self.sync_db()

    def sync_db(self):
        """Cüzdanı Buluttan/Yerelden çeker."""
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
        # 1. Gist'ten çekmeye çalış
        if GIST_ID:
            print(f"{Fore.CYAN}📡 Bulut cüzdanı (Gist) kontrol ediliyor...")
            try:
                r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
                if r.status_code == 200:
                    content = r.json()['files']['sazlik_cuzdan.json']['content']
                    return json.loads(content)
            except:
                pass # Hata olursa yerele dön

        # 2. Yerelden çek
        if os.path.exists(LOCAL_DB):
            print(f"{Fore.YELLOW}📂 Yerel cüzdan yüklendi.")
            with open(LOCAL_DB, 'r') as f:
                return json.load(f)

        # 3. Yoksa yeni oluştur
        print(f"{Fore.MAGENTA}✨ Yeni Forward Test cüzdanı oluşturuldu.")
        # Başlangıç bakiyesi 10.000$ (Test için)
        return {"bakiye": 10000.0, "portfoy": {}, "cezalar": {}, "gecmis_islemler": []}

    def save_db(self):
        """Cüzdanı kaydeder."""
        # Yerele yaz
        with open(LOCAL_DB, 'w') as f:
            json.dump(self.db, f, indent=4)
        print(f"{Fore.YELLOW}💾 Yerel dosya güncellendi.")
        
        # Buluta yaz
        if GITHUB_TOKEN and GIST_ID:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            data = {"files": {"sazlik_cuzdan.json": {"content": json.dumps(self.db, indent=4)}}}
            try:
                requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=data)
                print(f"{Fore.GREEN}☁️ Bulut cüzdanı güncellendi.")
            except Exception as e:
                print(f"{Fore.RED}⚠️ Bulut hatası: {e}")

    def run_cycle(self):
        print(f"\n{Fore.YELLOW}📡 SAZLIK FORWARD TEST: Delikanlı Modu... {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        bugun = datetime.now().strftime('%Y-%m-%d')
        
        # ----------------------------------------------------------------
        # 1. AŞAMA: MEVCUT PORTFÖYÜ KONTROL ET (SATILACAK VAR MI?)
        # ----------------------------------------------------------------
        if self.db['portfoy']:
            print(f"{Fore.CYAN}📋 Portföy ve Kâr/Zarar Kontrolü...")
            satilacaklar = []
            
            # Anlık fiyatları çekmek için yfinance kullanabiliriz veya news_bot içindeki veriyi
            # Basitlik adına burda hızlıca ticker sorguluyoruz
            import yfinance as yf
            
            for sembol, veri in list(self.db['portfoy'].items()):
                try:
                    ticker = yf.Ticker(sembol)
                    hist = ticker.history(period="1d")
                    if hist.empty: continue
                    
                    guncel_fiyat = float(hist['Close'].iloc[-1])
                    maliyet = veri['maliyet']
                    adet = veri['adet']
                    
                    # PNL Hesabı
                    pnl_yuzde = (guncel_fiyat - maliyet) / maliyet
                    pnl_tutar = (guncel_fiyat - maliyet) * adet
                    
                    renk = Fore.GREEN if pnl_yuzde > 0 else Fore.RED
                    print(f"   🔹 {sembol}: {guncel_fiyat:.2f}$ | Maliyet: {maliyet:.2f}$ | PNL: {renk}%{pnl_yuzde*100:.2f} ({pnl_tutar:.1f}$)")

                    # SATIŞ KURALLARI (TP/SL)
                    sebep = ""
                    if pnl_yuzde >= KAR_AL: sebep = "KÂR AL (%5)"
                    elif pnl_yuzde <= -ZARAR_KES: sebep = "ZARAR KES (%3)"
                    
                    if sebep:
                        satilacaklar.append((sembol, guncel_fiyat, sebep))
                        
                except Exception as e:
                    print(f"   ⚠️ {sembol} fiyat çekme hatası: {e}")

            # Satışları Gerçekleştir
            for sembol, fiyat, sebep in satilacaklar:
                adet = self.db['portfoy'][sembol]['adet']
                tutar = adet * fiyat
                self.db['bakiye'] += tutar
                del self.db['portfoy'][sembol]
                
                # Geçmişe işle
                self.db['gecmis_islemler'].append({
                    "tarih": bugun, "sembol": sembol, "islem": "SATIS", 
                    "fiyat": fiyat, "sebep": sebep
                })
                print(f"{Fore.MAGENTA}🔴 SATIŞ YAPILDI: {sembol} | {sebep} | Tutar: {tutar:.2f}$")
        
        # ----------------------------------------------------------------
        # 2. AŞAMA: YENİ TARAMA YAP (ALINACAK VAR MI?)
        # ----------------------------------------------------------------
        print(f"{Fore.CYAN}🔥 Piyasa Taranıyor (News Bot Motoru)... Bekleyiniz.")
        
        try:
            # Eski sonuç dosyasını temizle
            if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
            
            # MOTORU ÇALIŞTIR! (Bu işlem biraz sürer)
            bulunan_sayisi = news_bot.run_news_bot()
            
            if bulunan_sayisi > 0 and os.path.exists(OUTPUT_FILE):
                df = pd.read_csv(OUTPUT_FILE)
                
                # FİLTRE: Sadece 80 Puan ve Üzeri
                df_elite = df[df['Guven_Skoru'] >= MIN_PUAN_LIMITI].copy()
                
                # Zaten portföyde olanları ele
                portfoydeki_hisseler = list(self.db['portfoy'].keys())
                df_elite = df_elite[~df_elite['Hisse'].isin(portfoydeki_hisseler)]
                
                if df_elite.empty:
                    print(f"{Fore.YELLOW}⚠️ 80 Puan üzeri hisse bulundu ama hepsi zaten portföyde veya kriter dışı.")
                else:
                    # En iyi 6 taneyi al (Forward test için odaklanalım)
                    df_final = df_elite.sort_values(by='Guven_Skoru', ascending=False).head(6)
                    
                    toplam_skor = df_final['Guven_Skoru'].sum()
                    mevcut_bakiye = self.db['bakiye']
                    
                    # Eğer bakiye çok azsa işlem yapma
                    if mevcut_bakiye < 100:
                        print(f"{Fore.RED}⚠️ Bakiye yetersiz ({mevcut_bakiye:.2f}$). İşlem yapılamıyor.")
                    else:
                        print(f"{Fore.GREEN}✅ {len(df_final)} adet Elite Hisse bulundu. Alım yapılıyor...")
                        
                        for row in df_final.itertuples():
                            hisse = row.Hisse
                            puan = row.Guven_Skoru
                            fiyat = row.Fiyat
                            
                            # --- FORMÜL: PUAN ORANLI KASA YÖNETİMİ ---
                            # (Hisse Puanı / Toplam Puan) * Kasa
                            # Not: Bu, kasadaki TÜM parayı dağıtır.
                            pay = (puan / toplam_skor) * mevcut_bakiye
                            
                            # Adet hesabı
                            adet = int(pay / fiyat)
                            
                            if adet > 0:
                                maliyet = adet * fiyat
                                self.db['bakiye'] -= maliyet
                                self.db['portfoy'][hisse] = {
                                    'adet': adet, 
                                    'maliyet': fiyat, 
                                    'tarih': bugun,
                                    'puan': puan
                                }
                                self.db['gecmis_islemler'].append({
                                    "tarih": bugun, "sembol": hisse, "islem": "ALIS", 
                                    "fiyat": fiyat, "adet": adet, "puan": puan
                                })
                                print(f"{Fore.GREEN}🚀 ALIM: {hisse} | Skor: {puan} | Fiyat: {fiyat} | Yatırım: {maliyet:.2f}$")

            else:
                print(f"{Fore.RED}❌ Kriterlere uyan hisse bulunamadı (Puanlar düşük).")
                
        except Exception as e:
            print(f"{Fore.RED}⚠️ Tarama motoru hatası: {e}")

        # Kaydet ve Çık
        self.save_db()
        print("="*60)

if __name__ == "__main__":
    bot = SazlikForwardBot()
    bot.run_cycle()