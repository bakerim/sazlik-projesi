import yfinance as yf
import pandas as pd
import numpy as np
from colorama import Fore, Style, init
from datetime import datetime, timedelta
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
init(autoreset=True)

# --- İKİ AYRI KASA VE AYARLAR ---
SERMAYE_AMIRAL = 10000        
SERMAYE_GUVEN = 10000          
MAX_SLOT_PER_TABLE = 10       # Her masa kasasını 10'a böler (İşlem başı 1000$)
KOMISYON = 3.0         
START_DATE = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
END_DATE = datetime.now().strftime('%Y-%m-%d')

WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", 
    "MU", "WDC", "INTC", "QCOM", "AVGO", "TXN", "ADI", "MCHP",
    "JPM", "BAC", "C", "WFC", "GS", "MS", "V", "MA", "AXP",
    "XOM", "CVX", "COP", "EOG", "OXY", "SLB", "HAL", "BKR",
    "LLY", "UNH", "JNJ", "PFE", "MRK", "ABBV", "AMGN", "GILD",
    "NFLX", "CRM", "ADBE", "PYPL", "SQ", "SHOP", "ROKU", "SE",
    "SPOT", "UBER", "ABNB", "BKNG", "TGT", "WMT", "COST", "HD"
]

class SazlikCiftKasaBacktest:
    def __init__(self, symbols):
        self.symbols = list(set(symbols))
        self.kasa_amiral = SERMAYE_AMIRAL
        self.kasa_guven = SERMAYE_GUVEN
        self.acik_islemler = []
        self.islem_gecmisi = []
        self.data_store = {}

    def calculate_r2_and_slope(self, y_vals):
        if len(y_vals) < 20: return 0, 0
        y = np.array(y_vals)
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        return r2, slope

    def verileri_hazirla(self):
        print(f"{Fore.CYAN}⏳ Ağ atılıyor... 2 Yıllık veriler indiriliyor...{Style.RESET_ALL}")
        data = yf.download(self.symbols, start=START_DATE, end=END_DATE, progress=False)['Close']
        for sembol in self.symbols:
            if sembol in data.columns:
                df = pd.DataFrame({'Close': data[sembol]}).dropna()
                if len(df) > 200:
                    df['SMA50'] = df['Close'].rolling(50).mean()
                    df['SMA200'] = df['Close'].rolling(200).mean()
                    self.data_store[sembol] = df
        print(f"{Fore.GREEN}✔ Veri hazırlığı tamam. Çift Kasa Simülasyonu başlıyor...\n{Style.RESET_ALL}")

    def run(self):
        self.verileri_hazirla()
        all_dates = sorted(list(set(d for df in self.data_store.values() for d in df.index)))
        start_idx = 200 
        
        for current_date in all_dates[start_idx:]:
            # 1. ÇIKIŞ STRATEJİSİ
            for poz in self.acik_islemler[:]:
                sembol = poz['sembol']
                if current_date not in self.data_store[sembol].index: continue
                
                guncel_fiyat = self.data_store[sembol].loc[current_date, 'Close']
                guncel_sma50 = self.data_store[sembol].loc[current_date, 'SMA50']
                vade_takvim = (current_date - poz['tarih']).days
                
                cikis_fiyati = None
                neden = ""
                
                if poz['masa'] == "⚓ AMİRAL":
                    if guncel_fiyat <= poz['stop']:
                        cikis_fiyati = poz['stop']; neden = "ANA STOP PATLADI"
                    elif guncel_fiyat < guncel_sma50 and vade_takvim > 10: 
                        cikis_fiyati = guncel_fiyat; neden = "TREND BİTTİ"
                
                elif poz['masa'] == "🛡️ GÜVEN":
                    if guncel_fiyat >= poz['hedef']:
                        cikis_fiyati = poz['hedef']; neden = "KAR ALINDI"
                    elif guncel_fiyat <= poz['stop']:
                        cikis_fiyati = poz['stop']; neden = "ZARAR KES"
                    elif vade_takvim >= 7:
                        cikis_fiyati = guncel_fiyat; neden = "ZAMAN STOPU"
                    
                if cikis_fiyati:
                    brut_donus = cikis_fiyati * poz['adet']
                    net_donus = brut_donus - KOMISYON
                    if poz['masa'] == "⚓ AMİRAL": self.kasa_amiral += net_donus
                    else: self.kasa_guven += net_donus
                    
                    pnl_dolar = net_donus - poz['yatirim']
                    self.islem_gecmisi.append({
                        'Masa': poz['masa'], 'Sembol': sembol, 'Vade': vade_takvim,
                        'Net_PNL_$': pnl_dolar, 'Net_%': ((cikis_fiyati - poz['giris_fiyati']) / poz['giris_fiyati']) * 100,
                        'Sonuc': 'KAR' if pnl_dolar > 0 else 'ZARAR'
                    })
                    self.acik_islemler.remove(poz)

            # 2. GİRİŞ STRATEJİSİ
            acik_amiral = len([p for p in self.acik_islemler if p['masa'] == "⚓ AMİRAL"])
            acik_guven = len([p for p in self.acik_islemler if p['masa'] == "🛡️ GÜVEN"])
            
            for sembol, df in self.data_store.items():
                if current_date not in df.index: continue
                if any(p['sembol'] == sembol for p in self.acik_islemler): continue
                
                loc_idx = df.index.get_loc(current_date)
                curr = df.iloc[loc_idx]['Close']
                sma50 = df.iloc[loc_idx]['SMA50']
                sma200 = df.iloc[loc_idx]['SMA200']
                
                if curr > sma50:
                    son_20_kapanis = df.iloc[loc_idx-19:loc_idx+1]['Close'].values
                    r2, slope = self.calculate_r2_and_slope(son_20_kapanis)
                    
                    # ⚓ AMİRAL (Sınırsız Trend)
                    if curr > sma200 and sma50 > sma200 and r2 > 0.60 and acik_amiral < MAX_SLOT_PER_TABLE:
                        yatirim = self.kasa_amiral / (MAX_SLOT_PER_TABLE - acik_amiral)
                        if yatirim > 100:
                            self.kasa_amiral -= yatirim
                            self.acik_islemler.append({
                                'masa': "⚓ AMİRAL", 'sembol': sembol, 'adet': (yatirim-KOMISYON)/curr,
                                'giris_fiyati': curr, 'yatirim': yatirim, 'hedef': float('inf'), 'stop': curr*0.90, 'tarih': current_date
                            })
                            acik_amiral += 1
                        
                    # 🛡️ GÜVEN (Eski Hızlı Momentum)
                    elif slope > 0 and r2 > 0.65 and acik_guven < MAX_SLOT_PER_TABLE:
                        yatirim = self.kasa_guven / (MAX_SLOT_PER_TABLE - acik_guven)
                        if yatirim > 100:
                            self.kasa_guven -= yatirim
                            self.acik_islemler.append({
                                'masa': "🛡️ GÜVEN", 'sembol': sembol, 'adet': (yatirim-KOMISYON)/curr,
                                'giris_fiyati': curr, 'yatirim': yatirim, 'hedef': curr*1.05, 'stop': curr*0.97, 'tarih': current_date
                            })
                            acik_guven += 1

        self.raporla()

    def raporla(self):
        df = pd.DataFrame(self.islem_gecmisi)
        print("="*60)
        print(f"{Fore.GREEN}🦅 SAZLIK V23 - ÇİFT KASA BACKTEST (2 YILLIK){Style.RESET_ALL}")
        print("="*60)
        print(f"⚓ AMİRAL MASASI  | Final: {Fore.YELLOW}{self.kasa_amiral:.2f} ${Style.RESET_ALL} (Başlangıç: {SERMAYE_AMIRAL}$)")
        print(f"🛡️ GÜVEN MASASI   | Final: {Fore.YELLOW}{self.kasa_guven:.2f} ${Style.RESET_ALL} (Başlangıç: {SERMAYE_GUVEN}$)")
        print("-" * 60)
        
        for m in ["⚓ AMİRAL", "🛡️ GÜVEN"]:
            m_df = df[df['Masa'] == m]
            if not m_df.empty:
                wr = (len(m_df[m_df['Sonuc'] == 'KAR']) / len(m_df) * 100)
                print(f"{m} -> İşlem: {len(m_df)} | Başarı: %{wr:.1f} | Net PnL: {m_df['Net_PNL_$'].sum():.2f} $")

if __name__ == "__main__":
    bot = SazlikCiftKasaBacktest(WATCHLIST)
    bot.run()