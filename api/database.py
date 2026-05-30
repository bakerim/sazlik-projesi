from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta

# Veritabanımız dışarıya kapalı olarak projenin içinde oluşacak
SQLALCHEMY_DATABASE_URL = "sqlite:///./sazlik_kapali_devre.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Kullanıcılar Tablosu
class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(String, unique=True, index=True) # Örn: SZLK-001
    sifre_hash = Column(String) # Şifrelerin kırılmaz hali
    abonelik_bitis = Column(Date)
    rol = Column(String, default="abone") # admin veya abone
    # ... (önceki kodların altına ekle) ...

class AnalizSonucu(Base):
    __tablename__ = "analiz_sonuclari"

    id = Column(Integer, primary_key=True, index=True)
    masa_adi = Column(String, index=True) # "Amiral Masası" veya "Güven Masası"
    hisse = Column(String)                # Örn: AAPL, NVDA
    guven_skoru = Column(Integer)         # Örn: 85
    durum = Column(String)                # Örn: "Güçlü Trend"
    guncellenme_tarihi = Column(Date, default=datetime.utcnow)