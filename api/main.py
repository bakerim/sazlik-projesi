from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
import random
import string
import jwt

# Veritabanı bağlantıları
from .database import engine, Base, SessionLocal, Kullanici, AnalizSonucu

# Veritabanı tablolarını otomatik oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sazlık VIP API", version="1.0")

# --------- GÜVENLİK İZNİ (CORS - Flutter Bağlantısı İçin) ---------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Arayüzün API ile konuşmasına izin verir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- ŞİFRELEME VE BİLET (JWT) AYARLARI ---------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "sazlik_cok_gizli_kale_anahtari_2026" 
ALGORITHM = "HS256"

# Gümrük Memuru (Bileti kontrol eden yapı)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------- ANA SAYFA ---------
@app.get("/")
def ana_sayfa():
    return {"mesaj": "Sazlık VIP API Merkezi Beyin Aktif. Sistem Güvende ve Kapalı Devre."}

# --------- ADMIN KONTROL MERKEZİ (Müşteri Yönetimi) ---------
class YeniMusteriTalebi(BaseModel):
    kullanici_id: str
    abonelik_gun_sayisi: int

@app.post("/admin/musteri-yarat")
def musteri_yarat(talep: YeniMusteriTalebi, db: Session = Depends(get_db)):
    rastgele_sifre = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    sifre_hash = pwd_context.hash(rastgele_sifre)
    bitis_tarihi = datetime.now().date() + timedelta(days=talep.abonelik_gun_sayisi)
    
    yeni_kullanici = Kullanici(
        kullanici_id=talep.kullanici_id,
        sifre_hash=sifre_hash,
        abonelik_bitis=bitis_tarihi,
        rol="abone"
    )
    db.add(yeni_kullanici)
    db.commit()

    return {
        "mesaj": "Müşteri başarıyla oluşturuldu!",
        "musteriye_verilecek_bilgiler": {
            "Giris ID": talep.kullanici_id,
            "Sifre": rastgele_sifre,
            "Abonelik Bitis": bitis_tarihi
        }
    }

@app.get("/admin/musteriler")
def musterileri_listele(db: Session = Depends(get_db)):
    kullanicilar = db.query(Kullanici).all()
    liste = []
    for k in kullanicilar:
        liste.append({
            "kullanici_id": k.kullanici_id,
            "abonelik_bitis": str(k.abonelik_bitis), # Flutter'a metin formatında gönderiyoruz
            "rol": k.rol
        })
    return liste

# --------- GİRİŞ YAP VE BİLET AL (LOGIN) ---------
@app.post("/login")
def giris_yap(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    kullanici = db.query(Kullanici).filter(Kullanici.kullanici_id == form_data.username).first()
    if not kullanici:
        raise HTTPException(status_code=400, detail="Hatalı ID veya Şifre")
    
    if not pwd_context.verify(form_data.password, kullanici.sifre_hash):
        raise HTTPException(status_code=400, detail="Hatalı ID veya Şifre")
        
    if kullanici.abonelik_bitis < datetime.now().date():
        raise HTTPException(status_code=403, detail="Abonelik süreniz dolmuş!")

    bilet_verisi = {"sub": kullanici.kullanici_id, "exp": datetime.utcnow() + timedelta(hours=24)}
    token = jwt.encode(bilet_verisi, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": token, "token_type": "bearer"}

# --------- GÜMRÜK KONTROLÜ ---------
def yetki_kontrol(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        kullanici_id: str = payload.get("sub")
        if kullanici_id is None:
            raise HTTPException(status_code=401, detail="Geçersiz Bilet")
        return kullanici_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Biletin Süresi Dolmuş")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz Bilet")

# --------- BOTUN GİZLİ KAPISI (Gerçek Veri Yükleme) ---------
class YeniAnalizTalebi(BaseModel):
    masa_adi: str
    hisse: str
    guven_skoru: int
    durum: str

@app.post("/admin/analiz-yukle")
def analiz_yukle(talep: YeniAnalizTalebi, db: Session = Depends(get_db)):
    yeni_analiz = AnalizSonucu(
        masa_adi=talep.masa_adi,
        hisse=talep.hisse,
        guven_skoru=talep.guven_skoru,
        durum=talep.durum
    )
    db.add(yeni_analiz)
    db.commit()
    return {"mesaj": f"{talep.hisse} analizi {talep.masa_adi} veritabanına başarıyla yazıldı!"}

# --------- KİLİTLİ AMERİKAN BORSASI ANALİZ MASALARI (Gerçek Veri Okuma) ---------
@app.get("/api/analiz/amiral")
def amiral_masasi_getir(mevcut_kullanici: str = Depends(yetki_kontrol), db: Session = Depends(get_db)):
    sonuclar = db.query(AnalizSonucu).filter(AnalizSonucu.masa_adi == "Amiral Masası").all()
    return sonuclar

@app.get("/api/analiz/guven")
def guven_masasi_getir(mevcut_kullanici: str = Depends(yetki_kontrol), db: Session = Depends(get_db)):
    sonuclar = db.query(AnalizSonucu).filter(AnalizSonucu.masa_adi == "Güven Masası").all()
    return sonuclar