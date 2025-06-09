from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
import numpy as np
import torch
import os
import hashlib # // CHANGE !!

# === Kitap Öneri Sistemi Sınıfı ===
class BookRecommender:
    def __init__(self, csv_path, bert_path='data/bert_embeddings.npy'):
        self.df = pd.read_csv(csv_path).iloc[0:10000]
        self.df['Book-Title'] = self.df['Book-Title'].fillna('')
        self.df['Book-Author'] = self.df['Book-Author'].fillna('')
        self.df['combined'] = self.df['Book-Title'] + ' ' + self.df['Book-Author']

        # TF-IDF modeli
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.tfidf.fit_transform(self.df['combined'])

        # BERT modeli
        self.bert_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Vektörleri yükle veya oluştur
        if os.path.exists(bert_path):
            print(f"[INFO] BERT vektörleri {bert_path} dosyasından yükleniyor...")
            self.bert_embeddings = torch.tensor(np.load(bert_path))
        else:
            print(f"[INFO] BERT vektörleri oluşturuluyor ve {bert_path} dosyasına kaydediliyor...")
            self.bert_embeddings = self.bert_model.encode(self.df['combined'], convert_to_tensor=True)
            np.save(bert_path, self.bert_embeddings.cpu().numpy())

    def recommend_tfidf(self, query, n=5):
        query_vec = self.tfidf.transform([query])
        sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_idx = sim.argsort()[-n:][::-1]
        results = self.df.iloc[top_idx][['Book-Title', 'Book-Author']]
        results['Similarity'] = sim[top_idx]
        return results.to_dict(orient="records")

    def recommend_bert(self, query, n=5):
        query_emb = self.bert_model.encode(query, convert_to_tensor=True, device="cpu")

        # Eğer embedding'ler GPU'daysa, CPU'ya al
        if self.bert_embeddings.device.type != "cpu":
            self.bert_embeddings = self.bert_embeddings.cpu()

        cos_scores = util.pytorch_cos_sim(query_emb, self.bert_embeddings)[0]
        top_idx = np.argsort(-cos_scores.cpu())[:n]
        results = self.df.iloc[top_idx][['Book-Title', 'Book-Author']]
        results['Similarity'] = cos_scores[top_idx].cpu().numpy()
        return results.to_dict(orient="records")

# === Database Helper Class === # // CHANGE !!
class Database:
    def __init__(self, db_path='data/veritabanim.db'):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def kullanici_ekle(self, kullanici_adi, parola, email):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Parolayı hash'le
        parola_hash = hashlib.sha256(parola.encode()).hexdigest()

        cursor.execute("INSERT INTO kullanicilar (kullanici_adi, parola_hash, email) VALUES (?, ?, ?)", 
                      (kullanici_adi, parola_hash, email))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def tum_kullanicilari_getir(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, kullanici_adi, email FROM kullanicilar")
        kullanicilar = cursor.fetchall()
        conn.close()
        return kullanicilar

    def kitap_ekle(self, kullanici_id, baslik, yazar, yayinevi=None, yil=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO kitaplar (kullanici_id, baslik, yazar, yayinevi, yil) VALUES (?, ?, ?, ?, ?)",
                      (kullanici_id, baslik, yazar, yayinevi, yil))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def kullanici_kitaplarini_getir(self, kullanici_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kitaplar WHERE kullanici_id = ?", (kullanici_id,))
        kitaplar = cursor.fetchall()
        conn.close()
        return kitaplar

# === FastAPI Başlat ===
app = FastAPI()

# === CORS AYARI ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend'ten gelen istekler
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Modeli başta yükle ===
recommender = BookRecommender('data/unique_books.csv')
db = Database() # // CHANGE !!

# === API endpointleri ===
@app.get("/")
def read_root():
    return {"message": "Kitap öneri API'sine hoşgeldiniz!"}

@app.get("/recommend/")
def recommend_books(query: str, n: int = 5):
    tfidf_results = recommender.recommend_tfidf(query, n)
    bert_results = recommender.recommend_bert(query, n)
    return {
        "query": query,
        "tfidf_recommendations": tfidf_results,
        "bert_recommendations": bert_results
    }

# === Kullanıcı işlemleri === # // CHANGE !!
@app.post("/kullanici/ekle/")
def kullanici_ekle_endpoint(kullanici_adi: str, parola: str, email: str):
    kullanici_id = db.kullanici_ekle(kullanici_adi, parola, email)
    return {"id": kullanici_id, "message": "Kullanıcı başarıyla eklendi"}

@app.get("/kullanici/listele/")
def kullanici_listele():
    kullanicilar = db.tum_kullanicilari_getir()
    return {"kullanicilar": kullanicilar}

# === Kitap işlemleri === # // CHANGE !!
@app.post("/kitap/ekle/")
def kitap_ekle_endpoint(kullanici_id: int, baslik: str, yazar: str, yayinevi: str = None, yil: int = None):
    kitap_id = db.kitap_ekle(kullanici_id, baslik, yazar, yayinevi, yil)
    return {"id": kitap_id, "message": "Kitap başarıyla eklendi"}

@app.get("/kitap/listele/{kullanici_id}")
def kullanici_kitaplari(kullanici_id: int):
    kitaplar = db.kullanici_kitaplarini_getir(kullanici_id)
    return {"kitaplar": kitaplar}

# Veritabanına bağlanma // CHANGE !!
# conn = sqlite3.connect('data/veritabanim.db')
# cursor = conn.cursor()

# Veri ekleme örneği // CHANGE !!
# def kullanici_ekle(ad, soyad):
#     cursor.execute("INSERT INTO kullanicilar (ad, soyad) VALUES (?, ?)", 
#                   (ad, soyad))
#     conn.commit()
#     return cursor.lastrowid

# Veri sorgulama örneği // CHANGE !!
# def tum_kullanicilari_getir():
#     cursor.execute("SELECT * FROM kullanicilar")
#     return cursor.fetchall()

# Kullanım örnekleri // CHANGE !!
# yeni_id = kullanici_ekle("Mehmet", "Yılmaz")
# print(f"Yeni kullanıcı eklendi, ID: {yeni_id}")

# kullanicilar = tum_kullanicilari_getir()
# for kullanici in kullanicilar:
#     print(f"ID: {kullanici[0]}, Ad: {kullanici[1]}, Soyad: {kullanici[2]}")

# İşiniz bittiğinde bağlantıyı kapatmayı unutmayın // CHANGE !!
# conn.close()
@app.post("/kullanici/giris/")
def kullanici_giris(kullanici_adi: str = None, email: str = None, parola: str = None):
    if not parola or (not kullanici_adi and not email):
        return {"success": False, "message": "Kullanıcı adı/email ve parola gereklidir"}

    conn = sqlite3.connect('data/veritabanim.db')
    cursor = conn.cursor()

    # Kullanıcıyı bul (kullanıcı adı veya email ile)
    if kullanici_adi:
        cursor.execute("SELECT id, kullanici_adi, parola_hash, email FROM kullanicilar WHERE kullanici_adi = ?", 
                      (kullanici_adi,))
    else:
        cursor.execute("SELECT id, kullanici_adi, parola_hash, email FROM kullanicilar WHERE email = ?", 
                      (email,))

    kullanici = cursor.fetchone()
    conn.close()

    # Kullanıcı yoksa
    if not kullanici:
        return {"success": False, "message": "Kullanıcı bulunamadı"}

    # Gelen parolayı hash'le ve karşılaştır
    parola_hash = hashlib.sha256(parola.encode()).hexdigest()
    if kullanici[2] != parola_hash:
        return {"success": False, "message": "Parola yanlış"}

    # Başarılı giriş
    return {
        "success": True, 
        "message": "Giriş başarılı",
        "user": {
            "id": kullanici[0],
            "kullanici_adi": kullanici[1],
            "email": kullanici[3]
        }
    }
