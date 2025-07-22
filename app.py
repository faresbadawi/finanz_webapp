import sys
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from flask_frozen import Freezer

# --- Pfade ---
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "finance.db"

# --- Flask App & Freezer ---
app = Flask(__name__, static_folder="static")
freezer = Freezer(app)

# Verhindere das automatische Crawlen aller Links
freezer.crawl = False

# --- Datenbank initialisieren ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id   INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS incomes (
            id        INTEGER PRIMARY KEY,
            person_id INTEGER,
            source    TEXT,
            amount    REAL,
            FOREIGN KEY(person_id) REFERENCES persons(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id        INTEGER PRIMARY KEY,
            person_id INTEGER,
            desc      TEXT,
            amount    REAL,
            FOREIGN KEY(person_id) REFERENCES persons(id)
        )
    """)
    conn.commit()
    conn.close()

# --- Hilfsfunktion: Salden berechnen ---
def get_balances():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM persons")
    persons = c.fetchall()
    persons = [(None, "🔗 Gemeinsam")] + persons
    balances = []
    for pid, name in persons:
        c.execute("SELECT IFNULL(SUM(amount),0) FROM incomes WHERE person_id IS ?", (pid,))
        income = c.fetchone()[0]
        c.execute("SELECT IFNULL(SUM(amount),0) FROM expenses WHERE person_id IS ?", (pid,))
        expense = c.fetchone()[0]
        balances.append((name, income - expense))
    conn.close()
    return balances

# --- Routen ---
@app.route("/", methods=["GET", "POST"])
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == "POST":
        typ       = request.form["type"]
        pid       = request.form.get("person_id")
        person_id = None if pid in (None, "None") else int(pid)
        desc      = request.form["source_desc"].strip()
        amount    = float(request.form["amount"] or 0)
        if typ == "income":
            c.execute(
                "INSERT INTO incomes (person_id, source, amount) VALUES (?,?,?)",
                (person_id, desc, amount)
            )
        else:
            c.execute(
                "INSERT INTO expenses (person_id, desc, amount) VALUES (?,?,?)",
                (person_id, desc, amount)
            )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    c.execute("SELECT id, name FROM persons")
    persons = c.fetchall()
    conn.close()
    balances = get_balances()
    return render_template("index.html", persons=persons, balances=balances)

@app.route("/add_person", methods=["POST"])
def add_person():
    name = request.form["person_name"].strip()
    if name:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO persons (name) VALUES (?)", (name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
    return redirect(url_for("index"))

# --- Freezer Generator: Nur die Startseite einfrieren ---
@freezer.register_generator
def url_generator():
    yield url_for('index')

# --- Main: starten oder einfrieren ---
if __name__ == "__main__":
    init_db()
    if len(sys.argv) > 1 and sys.argv[1] == "freeze":
        freezer.freeze()
    else:
        app.run(debug=True)
