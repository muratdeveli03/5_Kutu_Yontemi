# init_db.py
import sqlite3

DB = "database.db"

# Öğrenciler (code, adsoyad, sinif)
students = [
    ("2011", "Mehmet TOSUN", 2),
    ("2012", "Gülsüm IŞIK", 2),
    ("2013", "Zeynep BEKTAŞ", 2),
    ("3011", "Kerem ASMA", 3),
    ("3012", "Doruk BAHAR", 3),
    ("3013", "Hamza SAĞDIÇ", 3)
]

# Kelimeler formatı: (sinif, english, turkish|alternatives separated by ;)
words = [
    (2, "Hello", "Merhaba;Selam"),
    (2, "Bye!", "Hoşça kal;Güle güle"),
    (2, "pupil", "öğrenci;talebe"),
    (2, "book", "kitap"),
    (3, "Book", "Kitap"),
    (3, "Pen", "Kalem"),
    (3, "Chair", "Sandalye;Oturak")
]

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # tablolar: ogrenciler, kelimeler, ogrenci_kelimeler
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ogrenciler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        adsoyad TEXT NOT NULL,
        sinif INTEGER NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kelimeler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sinif INTEGER NOT NULL,
        english TEXT NOT NULL,
        turkish TEXT NOT NULL,
        UNIQUE(sinif, english)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ogrenci_kelimeler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ogrenci_id INTEGER NOT NULL,
        kelime_id INTEGER NOT NULL,
        kutu INTEGER NOT NULL DEFAULT 1,
        last_review TEXT,
        UNIQUE(ogrenci_id, kelime_id)
    )
    """)

    # Öğrencileri ekle (varsa ignore)
    cur.executemany("""
    INSERT OR IGNORE INTO ogrenciler (code, adsoyad, sinif) VALUES (?, ?, ?)
    """, students)

    # Kelimeleri ekle (sinif+english unique)
    cur.executemany("""
    INSERT OR IGNORE INTO kelimeler (sinif, english, turkish) VALUES (?, ?, ?)
    """, words)

    conn.commit()

    # Şimdi: tüm öğrencilere sınıfına uygun eksik kelimeleri 1. kutuda ekle (mevcut ilerleme korunur)
    # Öğrencileri al
    cur.execute("SELECT id, sinif FROM ogrenciler")
    ogrenciler = cur.fetchall()

    for ogr in ogrenciler:
        ogr_id = ogr[0]
        ogr_sinif = ogr[1]
        # o sınıfa ait kelimeler
        cur.execute("SELECT id FROM kelimeler WHERE sinif=?", (ogr_sinif,))
        klass_word_ids = [r[0] for r in cur.fetchall()]
        for kid in klass_word_ids:
            cur.execute("""
            INSERT OR IGNORE INTO ogrenci_kelimeler (ogrenci_id, kelime_id, kutu, last_review)
            VALUES (?, ?, 1, NULL)
            """, (ogr_id, kid))

    conn.commit()
    conn.close()
    print("✅ database.db oluşturuldu / güncellendi. Öğrenciler ve kelimeler yüklendi; yeni kelimeler 1. kutuda eklendi.")

if __name__ == "__main__":
    init_db()
