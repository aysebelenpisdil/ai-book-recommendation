import sqlite3
import os
import hashlib

# Proje dizinini alalım
proje_dizini = os.path.dirname(os.path.abspath(__file__))

# Mevcut data klasörünün yolunu belirleyelim
data_klasoru = os.path.join(proje_dizini, 'data')

# Veritabanı dosyasının tam yolu
veritabani_yolu = os.path.join(data_klasoru, 'veritabanim.db')

# Veritabanı dosyasını oluşturma
conn = sqlite3.connect(veritabani_yolu)
cursor = conn.cursor()

# Kullanıcılar tablosu
cursor.execute('''
CREATE TABLE IF NOT EXISTS kullanicilar (
    id INTEGER PRIMARY KEY,
    kullanici_adi TEXT UNIQUE NOT NULL,
    parola_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
)
''')

# Kitaplar tablosu
cursor.execute('''
CREATE TABLE IF NOT EXISTS kitaplar (
    id INTEGER PRIMARY KEY,
    kullanici_id INTEGER NOT NULL,
    baslik TEXT NOT NULL,
    yazar TEXT NOT NULL,
    yayinevi TEXT,
    yil INTEGER,
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar (id)
)
''')

# Değişiklikleri kaydedip bağlantıyı kapatalım
conn.commit()
conn.close()

print(f"Veritabanı başarıyla oluşturuldu: {veritabani_yolu}")
