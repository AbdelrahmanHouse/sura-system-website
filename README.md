# Sura System — دليل التشغيل والنشر

## 1) شكل المشروع

```
sura_system/
├── app.py              ← السيرفر (Python / Flask) + قاعدة البيانات
├── view_users.py       ← لعرض المستخدمين المحفوظين
├── requirements.txt
├── templates/index.html  ← الصفحة (مرحباً ← تسجيل الدخول)
└── static/style.css      ← التصميم (CSS)
```

## 2) التشغيل على جهازك

```bash
cd sura_system
python -m venv venv
# ويندوز:        venv\Scripts\activate
# ماك / لينكس:   source venv/bin/activate
pip install -r requirements.txt
python app.py
```

افتح المتصفح على: http://127.0.0.1:5000

## 3) كيف تتحفظ البيانات؟

- قاعدة البيانات SQLite، وهي ملف اسمه `sura_system.db` ينشأ تلقائياً أول ما تشغّل `app.py`.
- جدول `users`: الإيميل + الباسورد **مشفّر (hash)** + تاريخ التسجيل.
- جدول `logins`: كل عملية دخول (الوقت + الـ IP).
- أي إيميل جديد يدخل = يتسجل حسابه تلقائياً. نفس الإيميل بعد كده لازم يدخل بنفس الباسورد.
- لعرض البيانات: `python view_users.py`
- مهم: **خُد نسخة احتياطية** من `sura_system.db` بشكل دوري.

## 4) النشر على الإنترنت

### أ) الدومين
ملحوظة: **الدومين مينفعش يحتوي على underscore (_)**، فـ `Sura_System.com` غير مسموح.
استخدم `sura-system.com` أو `surasystem.com`. اشتريه من Namecheap أو GoDaddy أو Cloudflare.

### ب) السيرفر (الأسهل: VPS ويندوز/لينكس، مثل DigitalOcean أو Hetzner)
على سيرفر Ubuntu:

```bash
sudo apt update && sudo apt install -y python3-venv nginx certbot python3-certbot-nginx
# ارفع مجلد المشروع إلى /var/www/sura_system
cd /var/www/sura_system
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
gunicorn --bind 127.0.0.1:8000 app:app      # للتجربة
```

شغّله دائماً كخدمة: أنشئ الملف `/etc/systemd/system/sura.service`:

```ini
[Unit]
Description=Sura System
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/sura_system
ExecStart=/var/www/sura_system/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo chown -R www-data:www-data /var/www/sura_system
sudo systemctl enable --now sura
```

إعداد Nginx في `/etc/nginx/sites-available/sura`:

```nginx
server {
    server_name sura-system.com www.sura-system.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/sura /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### ج) ربط الدومين
في لوحة الدومين أضف سجل **A** يشير إلى IP السيرفر (للاسم `@` وللاسم `www`).

### د) HTTPS (ضروري لأن فيه باسوردات)
```bash
sudo certbot --nginx -d sura-system.com -d www.sura-system.com
```

بديل أسهل بدون إدارة سيرفر: **Render.com** أو **Railway** أو **PythonAnywhere**؛ ترفع المشروع، وأمر التشغيل `gunicorn app:app`، ثم تربط الدومين من إعداداتهم.
(تنبيه: بعض الخدمات المجانية تمسح الملفات عند إعادة التشغيل، فلازم تضيف Disk/Volume دائم لملف `sura_system.db`، أو تستخدم PostgreSQL.)

## 5) قبل ما تفتح الموقع للناس

- النسخة الحالية "تسجّل حساب جديد تلقائياً". لو عايز تسجيل منفصل أو تأكيد إيميل أو "نسيت الباسورد"، ده بيتضاف لاحقاً.
- شغّل `debug=False` في production (gunicorn بيعمل كده تلقائياً).
- لو عدد المستخدمين كبير أو عايز أكتر من سيرفر، انقل لـ PostgreSQL.
- خُد نسخة احتياطية من قاعدة البيانات، وقانونياً لو عندك مستخدمين فعليين اكتب صفحة سياسة خصوصية.
