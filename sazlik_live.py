import pandas as pd
import json
import os
import requests
import news_bot
from datetime import datetime
from colorama import Fore, Style, init
from config import GITHUB_TOKEN, GIST_ID

# Renkleri başlat
init(autoreset=True)

# --- AYARLAR ---
DEFAULT_FILENAME = "sazlik_portfolio.json"
ANALYSIS_FILE = "sazlik_analiz_sonuclari.csv"
MIN_YATIRIM = 1000
MAX_YATIRIM = 2000

# --- AKILLI GIST FONKSİYONLARI ---
def get_portfolio():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        response = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        if response.status_code == 200:
            files = response.json().get('files', {})
            
            # Gist'in içindeki ilk dosyanın adını otomatik bul
            if files:
                first_filename = list(files.keys())[0]
                content = files[first_filename].get('content', '{}')
                if not content: return {}
                return json.loads(content)
            else:
                return {}
        return {}
    except Exception as e:
        print(f"⚠️ Cüzdan Okuma Hatası: {e}")
        return {}

def save_portfolio(portfolio):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    current_filename = DEFAULT_FILENAME
    
    # Mevcut dosya adını bulmaya çalış
    try:
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
        if r.status_code == 200:
            files = r.json().get('files', {})
            if files:
                current_filename = list(files.keys())[0]
    except: pass

    # Kaydet
    data = {"files": {current_filename: {"content": json.dumps(portfolio, indent=4)}}}
    requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=data)

def calculate_investment_amount(score):
    if score >= 90: return MAX_YATIRIM
    elif score >= 85: return 1750
    elif score >= 80: return 1500
    else: return MIN_YATIRIM

def run_live_trader():
    print(f"\n📡 {Fore.MAGENTA}SAZLIK LIVE TRADER: Akıllı Cüzdan v2{Style.RESET_ALL}")
    
    print("📋 Portföy Kontrol Ediliyor...")
    portfolio = get_portfolio()
    
    if portfolio:
        print(f"   🔹 Mevcut Varlıklar: {', '.join(portfolio.keys())}")
    else:
        print("   🔹 Cüzdan Boş.")

    # Analiz Başlıyor
    news_bot.run_news_bot()
    
    try:
        df = pd.read_csv(ANALYSIS_FILE)
        top_picks = df.sort_values(by='Guven_Skoru', ascending=False).head(6)
        
        print(f"\n🚀 {Fore.CYAN}ALIM İŞLEMLERİ BAŞLIYOR (1000himBHs2000$)...{Style.RESET_ALL}")
        
        trade_count = 0
        for index, row in top_picks.iterrows():
            ticker = row['Hisse']
            score = row['Guven_Skoru']
            price = row['Fiyat']
            
            if score >= 75 and ticker not in portfolio:
                # Parça Hisse Hesabı
                yatirim_tutari = calculate_investment_amount(score)
                adet = round(yatirim_tutari / price, 4)
                
                portfolio[ticker] = {
                    "cost": price,
                    "shares": adet,
                    "date": str(datetime.now().date()),
                    "total_invested": yatirim_tutari
                }
                
                print(f"💰 {Fore.GREEN}ALIM:{Style.RESET_ALL} {ticker:<6} | Skor: {score} |  ({adet} Lot)")
                trade_count += 1
            elif ticker in portfolio:
                print(f"ℹ️  {ticker} zaten portföyde, pas geçildi.")
                
        if trade_count > 0:
            save_portfolio(portfolio)
            print(f"\n☁️  Bulut cüzdanı güncellendi ({trade_count} işlem).")
        else:
            print("\n🤷‍♂️ Yeni işlem yapılmadı.")
            
    except Exception as e:
        print(f"❌ İşlem Hatası: {e}")

if __name__ == "__main__":
    run_live_trader()
