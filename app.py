# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "change_this_secret"

DB = "database.db"

def get_db_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_student_progress(ogrenci_id):
    """Eğer öğrenci için bazı kelimeler yoksa (yeni kelime eklenmişse) onları 1. kutuda ekle."""
    conn = get_db_conn()
    cur = conn.cursor()
    # öğrenci sınıfı
    cur.execute("SELECT sinif FROM ogrenciler WHERE id=?", (ogrenci_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return
    sinif = r["sinif"]
    # o sınıfa ait tüm kelime id'leri
    cur.execute("SELECT id FROM kelimeler WHERE sinif=?", (sinif,))
    kelime_ids = [row["id"] for row in cur.fetchall()]
    for kid in kelime_ids:
        cur.execute("""
            INSERT OR IGNORE INTO ogrenci_kelimeler (ogrenci_id, kelime_id, kutu, last_review)
            VALUES (?, ?, 1, NULL)
        """, (ogrenci_id, kid))
    conn.commit()
    conn.close()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        code = request.form.get("code","").strip()
        if not code:
            flash("Lütfen öğrenci kodu girin.")
            return redirect(url_for("login"))
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM ogrenciler WHERE code=?", (code,))
        student = cur.fetchone()
        conn.close()
        if student:
            # put useful info in session
            session["ogrenci_id"] = student["id"]
            session["ogrenci_code"] = student["code"]
            session["ogrenci_name"] = student["adsoyad"]
            session["ogrenci_class"] = student["sinif"]
            # ensure progress for this student (in case new kelime eklendi after init)
            ensure_student_progress(student["id"])
            return redirect(url_for("menu"))
        else:
            flash("Kod bulunamadı.")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/menu")
def menu():
    if "ogrenci_id" not in session:
        return redirect(url_for("login"))
    student = {"name": session.get("ogrenci_name"), "class": session.get("ogrenci_class")}
    return render_template("menu.html", student=student)

@app.route("/dashboard")
def dashboard():
    if "ogrenci_id" not in session:
        return redirect(url_for("login"))
    ogr_id = session["ogrenci_id"]
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT ok.kutu, k.english, k.turkish
        FROM ogrenci_kelimeler ok
        JOIN kelimeler k ON ok.kelime_id = k.id
        WHERE ok.ogrenci_id=?
        ORDER BY ok.kutu ASC, k.english
    """, (ogr_id,))
    rows = cur.fetchall()
    conn.close()
    boxes = {i: [] for i in range(1,6)}
    for r in rows:
        boxes[r["kutu"]].append({"english": r["english"], "turkish": r["turkish"]})
    student = {"name": session.get("ogrenci_name"), "class": session.get("ogrenci_class")}
    return render_template("dashboard.html", boxes=boxes, student=student)

@app.route("/practice", methods=["GET","POST"])
def practice():
    if "ogrenci_id" not in session:
        return redirect(url_for("login"))
    ogr_id = session["ogrenci_id"]
    today = date.today().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()

    # POST: cevap geldi -> kaydet ve redirect (PRG)
    if request.method == "POST":
        try:
            progress_id = int(request.form["progress_id"])
        except (KeyError, ValueError):
            flash("Kelime bilgisi eksik. Lütfen tekrar deneyin.")
            return redirect(url_for("practice"))

        answer = request.form.get("answer","").strip().lower()
        # progress kaydını al (içinde kelime id var)
        cur.execute("""
            SELECT ok.id as progress_id, ok.kutu, k.id as kelime_id, k.english, k.turkish
            FROM ogrenci_kelimeler ok
            JOIN kelimeler k ON ok.kelime_id = k.id
            WHERE ok.id=?
        """, (progress_id,))
        row = cur.fetchone()
        if not row:
            flash("Kelime bulunamadı.")
            conn.close()
            return redirect(url_for("practice"))

        correct_answers = [t.strip().lower() for t in row["turkish"].split(";") if t.strip()]
        is_correct = answer in correct_answers
        new_kutu = min(row["kutu"] + 1, 5) if is_correct else row["kutu"]

        # güncelle
        cur.execute("""
            UPDATE ogrenci_kelimeler
            SET kutu=?, last_review=?
            WHERE id=?
        """, (new_kutu, today, progress_id))
        conn.commit()
        conn.close()

        if is_correct:
            flash(f"✅ Doğru! '{row['english']}' kelimesi {new_kutu}. kutuya geçti.")
        else:
            flash(f"❌ Yanlış. Doğru cevaplar: {', '.join(correct_answers)}. Kelime {new_kutu}. kutuda kaldı.")
        return redirect(url_for("practice"))

    # GET: kelime seç (5. kutu hariç, en ilerideki kutudan; box: 4->1)
    selected = None
    for kutu in range(4, 0, -1):
        cur.execute("""
            SELECT ok.id as progress_id, ok.kutu, k.id as kelime_id, k.english, k.turkish
            FROM ogrenci_kelimeler ok
            JOIN kelimeler k ON ok.kelime_id = k.id
            WHERE ok.ogrenci_id=? AND ok.kutu=? AND (ok.last_review IS NULL OR ok.last_review != ?)
            ORDER BY RANDOM() LIMIT 1
        """, (ogr_id, kutu, today))
        row = cur.fetchone()
        if row:
            selected = row
            break

    conn.close()

    if not selected:
        student = {"name": session.get("ogrenci_name"), "class": session.get("ogrenci_class")}
        return render_template("practice.html", done=True, student=student)

    # seçilen kelimeyi göster
    word = {"id": selected["kelime_id"], "english": selected["english"], "turkish": selected["turkish"], "progress_id": selected["progress_id"], "kutu": selected["kutu"]}
    student = {"name": session.get("ogrenci_name"), "class": session.get("ogrenci_class")}
    return render_template("practice.html", done=False, student=student, word=word)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
