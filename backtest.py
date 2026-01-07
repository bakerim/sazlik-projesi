import yfinance as yf
import pandas as pd
from colorama import Fore, Style, init
from datetime import datetime, timedelta

init(autoreset=True)

# --- AYARLAR ---
SERMAYE = 10000        
KOMISYON_AL = 1.5      
KOMISYON_SAT = 1.5     
CEZA_SURESI = 10       # Stop sonrası küsme süresi
START_DATE = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
END_DATE = datetime.now().strftime('%Y-%m-%d')


WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE", 
    "CRM", "CMCSA", "QCOM", "TXN", "AMGN", "INTC", "CSCO", "VZ", "T", "TMUS",
    "NFLX", "ORCL", "MU", "IBM", "PYPL", "INTU", "AMD", "FTNT", "ADI", "NOW",
    "LRCX", "MRVL", "CDNS", "SNPS", "DXCM", "KLAC", "ROST", "MSCI", "CHTR",
    "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPY", "BLK", "SCHW",
    "C", "AXP", "CB", "MMC", "AON", "CME", "ICE", "PGR", "ALL", "MET",
    "AIG", "PNC", "USB", "BK", "COF", "DFS", "TRV", "MCO", "CBOE", "RJF",
    "GPN", "FIS", "ZION", "FITB", "STT", "NDAQ", "RF", "KEY", "CFG", "HBAN",
    "JNJ", "LLY", "UNH", "ABBV", "MRK", "PFE", "DHR", "TMO", "MDT", "SYK",
    "GILD", "BIIB", "VRTX", "BMY", "ISRG", "ABT", "ZTS", "BDX", "BSX",
    "CI", "CVS", "HUM", "HCA", "LH", "COO", "ALGN", "HOLX", "DVA",
    "WAT", "RGEN", "IQV", "REGN", "EW", "TECH", "DGX", "INCY", "CRL",
    "PG", "KO", "PEP", "WMT", "COST", "HD", "MCD", "NKE", "LOW", "TGT",
    "SBUX", "MDLZ", "CL", "PM", "MO", "KR", "DG", "EL", "KHC",
    "GIS", "K", "SYY", "APO", "DECK", "BBY", "WHR", "NWSA", "FOXA", "HAS",
    "MAT", "HOG", "GT", "TPR", "TTC", "VFC", "HBI", "KSS", "ULTA",
    "XOM", "CVX", "LMT", "RTX", "BA", "HON", "MMM", "GE", "GD",
    "CAT", "DE", "EOG", "OXY", "COP", "PSX", "MPC", "WMB", "KMI",
    "ETN", "AOS", "EMR", "PCAR", "ROK", "SWK", "TDY", "RSG", "WM", "CARR",
    "ITW", "GWW", "WAB", "IEX", "AAL", "DAL", "UAL", "LUV", "ALK",
    "DUK", "NEE", "SO", "EXC", "AEP", "SRE", "WEC", "D", "ED", "XEL",
    "VNQ", "SPG", "PLD", "EQIX", "AMT", "CCI", "HST", "O", "ARE", "PSA",
    "WY", "BXP", "REG", "VTR", "AVB", "KIM", "FRT",
    "LUMN", "FOX", "EBAY", "EA", "TTWO", "ZG", "ASML", "AMAT", "TSM", "MCHP", 
    "TER", "U", "VEEV", "OKTA", "NET", "CRWD", "DDOG", "ZS", "TEAM", "ADSK", 
    "MSI", "FTV", "WDC", "ZBRA", "SWKS", "QDEL", "FSLY", "PLUG", "SEDG", 
    "RUN", "SPWR", "BLDP", "FCEL", "BE", "SOL", "LI", "NIO", "XPEV", "RIVN", 
    "LCID", "QS", "GOEV", "COIN", "HOOD", "UPST", "AFRM", "SOFI", "MQ", "BILL", 
    "TOST", "BRZE", "DOCU", "SABR", "TTEC", "TWLO", "RNG", "ZM", "MRNA", 
    "BMRN", "CTAS", "CORT", "EXEL", "IONS", "XBI", "LABU", "EDIT", "BEAM", 
    "NTLA", "CRSP", "MELI", "ROKU", "PTON", "SPOT", "CHWY", "FVRR", "PINS", 
    "WIX", "SHOP", "SE", "BABA", "JD", "BIDU", "PDD", "ROP", "TT", "FLR", 
    "HUBB", "APH", "ECL", "SHW", "PPG", "FMC", "MOS", "CF", "NUE", "STLD", 
    "RCL", "CCL", "NCLH", "MGM", "WYNN", "LVS", "PENN", "DKNG", "BYND",
    "RBLX", "UBER", "LYFT", "ABNB", "DOX", "PRU", "L", "VLO", "DVN", "APA", 
    "HAL", "BKR", "FTI", "NOV", "TDW", "PAGP", "PAA", "WES"
]

class SazlikProFinal:
    def __init__(self, symbols):
        self.symbols = list(set(symbols)) # Tekrarları temizle
        self.kasa = SERMAYE
        self.toplam_komisyon = 0
        self.islem_gecmisi = []
        self.toplam_islem = 0

    def calculate_indicators(self, df):
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['Price_20d_Ago'] = df['Close'].shift(20)
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        return df

    def run(self):
        print(f"{Fore.CYAN}🚀 Sazlık V5 (Temiz Liste) Başlatılıyor...")
        
        for symbol in self.symbols:
            try:
                ticker = symbol.replace('.', '-')
                df = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
                if df is None or len(df) < 50: continue
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

                df = self.calculate_indicators(df)
                
                # ALIM STRATEJİSİ
                df['Signal'] = (df['Close'] > df['Price_20d_Ago']) & \
                               (df['Close'] > df['SMA_20']) & \
                               (df['RSI'] < 70) & \
                               (df['Volume'] > df['Vol_SMA_20'])

                in_pos = False
                buy_p = 0
                ceza_bitis = None
                son_islem_tarih = None

                for i in range(21, len(df)):
                    tarih = df.index[i]
                    row = df.iloc[i]
                    price = float(row['Close'])

                    if son_islem_tarih and son_islem_tarih.date() == tarih.date(): continue
                    if ceza_bitis and tarih < ceza_bitis: continue

                    if not in_pos and row['Signal']:
                        in_pos = True
                        buy_p = price
                        buy_date = tarih
                        self.kasa -= KOMISYON_AL
                        self.toplam_komisyon += KOMISYON_AL
                    
                    elif in_pos:
                        pnl_oran = (price - buy_p) / buy_p
                        if pnl_oran >= 0.05 or pnl_oran <= -0.03:
                            self.kasa -= KOMISYON_SAT
                            self.toplam_komisyon += KOMISYON_SAT
                            net_pnl = (SERMAYE * pnl_oran) - (KOMISYON_AL + KOMISYON_SAT)
                            self.kasa += net_pnl
                            self.toplam_islem += 1
                            
                            if pnl_oran <= -0.03:
                                ceza_bitis = tarih + timedelta(days=CEZA_SURESI)
                            
                            self.islem_gecmisi.append({
                                'Sembol': symbol, 'PNL': net_pnl, 
                                'Sonuc': 'KAR' if pnl_oran > 0 else 'ZARAR'
                            })
                            in_pos = False
                            son_islem_tarih = tarih
            except: continue

        self.raporla()

    def raporla(self):
        df = pd.DataFrame(self.islem_gecmisi)
        win_rate = (len(df[df['Sonuc']=='KAR']) / len(df) * 100) if not df.empty else 0
        print("\n" + "="*50)
        print(f"{Fore.GREEN}💰 FİNAL KASA        : {self.kasa:.2f} $")
        print(f"📈 NET KAR           : {self.kasa - SERMAYE:.2f} $")
        print(f"📊 BAŞARI ORANI (WR) : %{win_rate:.2f}")
        print(f"🔄 TOPLAM İŞLEM      : {self.toplam_islem}")
        print(f"💸 TOPLAM KOMİSYON   : {self.toplam_komisyon:.2f} $")
        print("="*50)

if __name__ == "__main__":
    bot = SazlikProFinal(WATCHLIST)
    bot.run()