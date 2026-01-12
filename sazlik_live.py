import time
import json
import requests
import config
import news_bot
from datetime import datetime

# Renkler
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def get_data():
    headers = {"Authorization": f"token {config.GITHUB_TOKEN}"}
    try:
        r = requests.get(f"https://api.github.com/gists/{config.GIST_ID}", headers=headers)
        if r.status_code == 200:
            content = r.json()['files'][list(r.json()['files'].keys())[0]]['content']
            return json.loads(content)
    except Exception as e:
        print(f"Hata: {e}")
        return None

def run_live_trader():
    print(f"\n{Colors.HEADER}📡 SAZLIK LIVE TRADER: Akıllı Cüzdan v2{Colors.ENDC}")
    
    # 1. Cüzdan Kontrolü
    data = get_data()
    if data:
        print(f"{Colors.BLUE}📋 Portföy:{Colors.ENDC} {list(data.get('portfoy', {}).keys())}")
    
    # 2. Tarama Başlıyor
    print(f"\n{Colors.BLUE}🔍 Piyasa Taranıyor (Terminal Modu)...{Colors.ENDC}")
    
    ignore_list = ["PORTFOY", "CEZALAR", "KASA", "NAKIT", "TOPLAM", "YATIRIM"]
    watch_list = [t for t in config.WATCHLIST_TICKERS if t not in ignore_list]
    
    found_stocks = []
    
    # Döngüyle tek tek bakıyoruz
    for i, ticker in enumerate(watch_list):
        print(f"\rAnaliz: {ticker} ({i+1}/{len(watch_list)})", end="")
        
        # News_bot içindeki tekil analiz fonksiyonunu çağırıyoruz
        result = news_bot.analyze_stock(ticker)
        
        if result and result['Puan'] >= 50:
            print(f" -> ✅ {Colors.GREEN}ADAY: {ticker} ({result['Puan']:.1f}){Colors.ENDC}")
            found_stocks.append(result)
            
    print("\n\n🏁 Tarama Bitti.")
    
    if found_stocks:
        print(f"{Colors.GREEN}--- EN İYİ SONUÇLAR ---{Colors.ENDC}")
        # En iyi 5'i yazdır
        top_picks = sorted(found_stocks, key=lambda x: x['Puan'], reverse=True)[:5]
        for pick in top_picks:
            print(f"💰 {pick['Hisse']} | Puan: {pick['Puan']:.1f} | Fiyat: ${pick['Fiyat']:.2f}")

if __name__ == "__main__":
    run_live_trader()