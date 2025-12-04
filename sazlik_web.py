import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# --- MODÜL 1: HAFIZA (RETRIEVAL) ---
def get_past_context(ticker, archive_path='data/news_archive.json', lookback_days=30):
    """
    Belirtilen hisse için arşivdeki geçmiş haberleri getirir.
    RAG'ın 'Retrieval' kısmıdır.
    """
    try:
        # Arşiv dosyasını oku
        df = pd.read_json(archive_path)
        
        # Tarih formatını düzelt
        df['date'] = pd.to_datetime(df['date'])
        
        # Sadece ilgili hisseyi ve son X günü filtrele
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        mask = (df['ticker'] == ticker) & (df['date'] > cutoff_date)
        relevant_news = df.loc[mask].sort_values(by='date', ascending=True) # Eskiden yeniye
        
        if relevant_news.empty:
            return "Bu hisse ile ilgili yakın geçmişte (son 30 gün) kayıtlı bir haber akışı yok."
            
        # Bağlam metnini oluştur
        context_text = ""
        for _, row in relevant_news.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            # Eğer geçmiş analizde bir skor varsa onu da ekle
            past_score = row.get('ai_score', 'N/A') 
            context_text += f"- [{date_str}] Haber: {row['content']} (Önceki AI Skoru: {past_score})\n"
            
        return context_text

    except FileNotFoundError:
        return "Arşiv dosyası bulunamadı. Bu ilk analiz olabilir."
    except Exception as e:
        return f"Bağlam getirilirken hata oluştu: {str(e)}"

# --- MODÜL 2: TEKNİK GÖZ (SMART MONEY CHECK) ---
def get_technical_status(ticker):
    """
    Hissenin teknik durumunu (Ayı/Boğa piyasası, Aşırı Alım/Satım) kontrol eder.
    Haberin zamanlamasını yargılamak için kritiktir.
    """
    try:
        # BIST hisseleri için .IS ekle (Eğer kodda yoksa)
        symbol = f"{ticker}.IS" if not ticker.endswith(".IS") else ticker
        
        # Son 1 yıllık veriyi çek
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")
        
        if hist.empty:
            return "Teknik veri çekilemedi."
            
        current_price = hist['Close'].iloc[-1]
        
        # Hareketli Ortalamalar (Trend tespiti için)
        sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        
        # Trend Yorumu
        trend = "NÖTR"
        if current_price > sma200:
            trend = "YÜKSELİŞ TRENDİ (Boğa)" if current_price > sma50 else "DÜZELTME/YATAY"
        else:
            trend = "DÜŞÜŞ TRENDİ (Ayı)"
            
        # RSI Hesabı (Basitleştirilmiş - Aşırı alım/satım için)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        rsi_status = "Normal"
        if rsi > 70: rsi_status = "AŞIRI ALIM (Pahalı)"
        elif rsi < 30: rsi_status = "AŞIRI SATIM (Ucuz)"
            
        return f"Fiyat: {current_price:.2f} TL | Ana Trend: {trend} | RSI: {rsi:.1f} ({rsi_status})"
        
    except Exception as e:
        return f"Teknik analiz hatası: {str(e)}"

# --- MODÜL 3: BEYİN (PROMPT HAZIRLAMA) ---
def create_rag_prompt(ticker, new_news_content, past_context, technical_status):
    """
    Tüm verileri birleştirip LLM'e gidecek 'Bilimsel' promptu hazırlar.
    """
    system_prompt = f"""
SEN BİR SWING TRADE VE RİSK ANALİZ UZMANISIN.
Görevin: Aşağıdaki yeni haberi, hissenin geçmiş haber akışı ve mevcut teknik durumuyla HARMANLAYARAK analiz etmektir.

HEDEF: "{ticker}" hissesi için bu haberin kısa-orta vadeli (1-10 gün) etkisini öngörmek.

--- ANALİZ VERİLERİ ---

1. [CANLI TEKNİK DURUM] (Piyasa Gerçekliği):
{technical_status}
*(Dikkat: Eğer hisse "Aşırı Alım" bölgesindeyse, iyi haberler bile "Satış Fırsatı" olabilir. Trend "Ayı" ise iyi haberlerin etkisi sınırlı kalabilir.)*

2. [HAFIZA / BAĞLAM] (Son 30 Gün):
{past_context}
*(Dikkat: Bu yeni haber, geçmişteki bir hikayenin devamı mı? Yoksa sürpriz mi?)*

3. [YENİ HABER]:
"{new_news_content}"

--- İSTENEN ÇIKTI (SADECE JSON) ---
Lütfen sadece aşağıdaki JSON formatında yanıt ver, başka metin yazma:
{{
  "impact_score": (0 ile 100 arası, 50 nötr),
  "sentiment": "POZİTİF / NEGATİF / NÖTR",
  "reasoning": "Teknik veriler trendin X olduğunu gösteriyor, ancak geçmiş haberlerde Y olduğu için bu haber Z etkisi yaratabilir...",
  "action_suggestion": "İzlemeye Al / Kademeli Alım / Satış Fırsatı / İşlem Yapma",
  "estimated_duration": "Anlık Tepki / 1-3 Gün / Trend Değiştirici"
}}
"""
    return system_prompt
