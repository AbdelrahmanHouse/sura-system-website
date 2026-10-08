"""اعرض كل المستخدمين المحفوظين في قاعدة البيانات.
التشغيل:  python view_users.py
"""
import os
import sqlite3

db = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sura_system.db"))
rows = db.execute(
    """
    SELECT u.id, u.email, u.created_at, COUNT(l.id) AS logins
    FROM users u LEFT JOIN logins l ON l.user_id = u.id
    GROUP BY u.id ORDER BY u.id
    """
).fetchall()

print(f"عدد المستخدمين: {len(rows)}\n")
for r in rows:
    print(f"#{r[0]}  {r[1]}  | تاريخ التسجيل: {r[2]}  | عدد مرات الدخول: {r[3]}")
