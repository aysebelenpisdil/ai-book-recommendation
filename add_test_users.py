import sqlite3
import hashlib
import os

# Get project directory
project_dir = os.path.dirname(os.path.abspath(__file__))

# Database path
db_path = os.path.join(project_dir, 'data', 'veritabanim.db')

print(f"Looking for database at: {db_path}")

# If database doesn't exist, create it
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}. Creating database...")

    # Make sure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Create database and tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id INTEGER PRIMARY KEY,
        kullanici_adi TEXT UNIQUE NOT NULL,
        parola_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
    ''')

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

    conn.commit()
    conn.close()
    print(f"Database created at: {db_path}")

# Create test users function
def add_test_user(kullanici_adi, parola, email):
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Hash the password
    parola_hash = hashlib.sha256(parola.encode()).hexdigest()

    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM kullanicilar WHERE kullanici_adi = ? OR email = ?", 
                      (kullanici_adi, email))
        existing_user = cursor.fetchone()

        if existing_user:
            print(f"Kullanıcı zaten var: {kullanici_adi} / {email}")
            return False

        # Add the user
        cursor.execute(
            "INSERT INTO kullanicilar (kullanici_adi, parola_hash, email) VALUES (?, ?, ?)",
            (kullanici_adi, parola_hash, email)
        )
        conn.commit()
        print(f"Kullanıcı eklendi: {kullanici_adi}, {email}")
        return True

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False

    finally:
        conn.close()

# Add some test users
users = [
    ("admin", "admin123", "admin@example.com"),
    ("test_user", "password123", "test@example.com"),
    ("mehmet", "mehmet123", "mehmet@example.com")
]

# Add each test user
for user in users:
    add_test_user(*user)

# Verify users were added
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id, kullanici_adi, email FROM kullanicilar")
all_users = cursor.fetchall()
conn.close()

print("\nKullanıcı Listesi:")
for user in all_users:
    print(f"ID: {user[0]}, Kullanıcı Adı: {user[1]}, Email: {user[2]}")
