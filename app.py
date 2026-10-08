import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, g, jsonify, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sura_system.db")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- قاعدة البيانات ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS logins (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            ip         TEXT,
            logged_at  TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    db.commit()
    db.close()


init_db()


# ---------- الصفحات ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not EMAIL_RE.match(email):
        return jsonify(ok=False, message="الإيميل غير صحيح"), 400
    if len(password) < 6:
        return jsonify(ok=False, message="الباسورد لازم يكون 6 حروف على الأقل"), 400

    db = get_db()
    now = datetime.utcnow().isoformat(timespec="seconds")
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if user is None:
        # مستخدم جديد: نحفظ بياناته (الباسورد مشفّر وليس نصاً عادياً)
        cur = db.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, generate_password_hash(password), now),
        )
        user_id = cur.lastrowid
        message = "تم إنشاء حسابك وتسجيل دخولك بنجاح"
    else:
        if not check_password_hash(user["password_hash"], password):
            return jsonify(ok=False, message="الباسورد غير صحيح"), 401
        user_id = user["id"]
        message = "تم تسجيل الدخول بنجاح"

    # نسجل كل عملية دخول
    db.execute(
        "INSERT INTO logins (user_id, ip, logged_at) VALUES (?, ?, ?)",
        (user_id, request.headers.get("X-Forwarded-For", request.remote_addr), now),
    )
    db.commit()
    # اسم المستخدم = الجزء الذي قبل علامة @ في الإيميل
    name = email.split("@")[0]
    return jsonify(ok=True, message=message, email=email, name=name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
