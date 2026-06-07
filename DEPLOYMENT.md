# Deployment Guide — Bali Tattoo Studio (Django)

Aplikasi ini sudah dikonfigurasi untuk di-deploy di berbagai platform hosting **tanpa mengubah kode** — cukup atur environment variables yang sesuai.

## Daftar Isi

1. [Environment Variables (WAJIB)](#environment-variables)
2. [Deploy ke Hostinger (Shared / VPS)](#hostinger)
3. [Deploy ke Vercel (Serverless)](#vercel)
4. [Setup Custom Domain](#custom-domain)
5. [Setup Database Production](#database)
6. [Setup Media Storage (untuk Serverless)](#media-storage)
7. [Troubleshooting](#troubleshooting)

---

<a name="environment-variables"></a>
## 1. Environment Variables (WAJIB)

Salin `.env.example` ke `.env` (development) atau set di dashboard hosting (production):

| Variable | Wajib? | Keterangan |
|---|---|---|
| `SECRET_KEY` | ✅ | Generate baru: https://djecrety.ir atau `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | ✅ | `False` untuk production |
| `ALLOWED_HOSTS` | ✅ | Domain kamu. Contoh: `yourdomain.com,www.yourdomain.com,.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | ✅ | URL lengkap. Contoh: `https://yourdomain.com,https://www.yourdomain.com` |
| `DATABASE_URL` | Vercel ✅ | Untuk Vercel wajib PostgreSQL. Format: `postgres://user:pass@host:5432/db` |
| `CLOUDINARY_*` | Vercel ✅ | Untuk Vercel wajib Cloudinary (lihat section Media Storage) |
| `PAYMENT_EXPIRY_HOURS` | optional | Default 24 |
| `PAY_*` | optional | Rekening / e-wallet untuk payment instructions |

> ⚠️ **JANGAN PERNAH** commit file `.env` ke Git! Sudah ada di `.gitignore`.

---

<a name="hostinger"></a>
## 2. Deploy ke Hostinger (Shared / VPS)

Hostinger memiliki 2 cara deploy Python/Django:

### Cara A: Hostinger Shared Hosting + cPanel Python Selector (Recommended untuk pemula)

1. **Login ke hPanel Hostinger** → Hosting → Manage → cPanel
2. **Setup Python App**:
   - Pergi ke **Setup Python App** (Software section)
   - Klik **Create Application**
   - Python version: **3.10+** (3.12 recommended)
   - Application root: misal `tattoo_app`
   - Application URL: `/` (domain utama) atau subdomain
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`
   - Klik **Create**
3. **Upload project**:
   - Buka **File Manager** di cPanel
   - Navigasi ke `~/tattoo_app/` (atau path Application root)
   - Upload semua file project (kecuali yang tidak perlu: `db.sqlite3`, `staticfiles/`, `__pycache__/`, `.env`)
   - **ATAU** lebih mudah: gunakan **Git** di cPanel → connect ke GitHub repo
4. **Install dependencies**:
   - Kembali ke Setup Python App → klik **"Run Pip Install"** atau jalankan di Terminal:
     ```bash
     source /home/user/virtualenv/tattoo_app/3.12/bin/activate
     cd ~/tattoo_app
     pip install -r requirements.txt
     ```
5. **Setup environment variables**:
   - Di Setup Python App, scroll ke **Environment variables**
   - Tambahkan semua variable dari tabel di atas
6. **Jalankan migration & collectstatic** (via Terminal cPanel):
   ```bash
   cd ~/tattoo_app
   source /home/user/virtualenv/tattoo_app/3.12/bin/activate
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
7. **Restart Python App** di Setup Python App → klik **Restart**
8. **Selesai!** Buka domain kamu.

### Cara B: Hostinger VPS (lebih flexible)

```bash
# SSH ke VPS
ssh user@your-vps-ip

# Install dependencies
sudo apt update
sudo apt install python3.12 python3.12-venv nginx

# Setup project
cd /var/www
git clone https://github.com/youruser/tattoo.git tattoo
cd tattoo
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # edit sesuai konfigurasi

# Setup database (SQLite atau PostgreSQL)
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# Setup Gunicorn service
sudo nano /etc/systemd/system/tattoo.service
```
Isi `tattoo.service`:
```ini
[Unit]
Description=Tattoo Django App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/tattoo
Environment="PATH=/var/www/tattoo/venv/bin"
EnvironmentFile=/var/www/tattoo/.env
ExecStart=/var/www/tattoo/venv/bin/gunicorn --workers 3 --bind unix:/var/www/tattoo/tattoo.sock bisnis.wsgi:application

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl start tattoo
sudo systemctl enable tattoo

# Setup Nginx
sudo nano /etc/nginx/sites-available/tattoo
```
Isi nginx config:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /var/www/tattoo/staticfiles/;
    }

    location /media/ {
        alias /var/www/tattoo/media/;
    }

    location / {
        proxy_pass http://unix:/var/www/tattoo/tattoo.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/tattoo /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# SSL gratis dari Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

<a name="vercel"></a>
## 3. Deploy ke Vercel (Serverless)

> ⚠️ **PENTING untuk Vercel**: Filesystem tidak persistent. Jadi:
> - **WAJIB** pakai PostgreSQL (bukan SQLite)
> - **WAJIB** pakai Cloudinary untuk media (bukan local)

### Setup Database (Vercel butuh PostgreSQL)

Vercel Postgres sudah discontinued, jadi pakai salah satu (semua ada free tier):
- **[Neon](https://neon.tech)** — Recommended, paling mudah
- **[Supabase](https://supabase.com)**
- **[Railway Postgres](https://railway.app)**

Setelah signup, copy `DATABASE_URL` (format: `postgresql://user:password@host:5432/dbname`).

### Setup Cloudinary (untuk media files)

1. Signup gratis di https://cloudinary.com (free tier 25GB storage, 25GB bandwidth)
2. Di Dashboard, copy:
   - `Cloud Name`
   - `API Key`
   - `API Secret`

### Deploy

1. **Push project ke GitHub** (skip file yang tidak perlu):
   ```bash
   cd proyek-tattoo
   ```
   Pastikan `.gitignore` ada:
   ```
   .env
   db.sqlite3
   staticfiles/
   media/
   __pycache__/
   *.pyc
   .venv/
   venv/
   ```
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/youruser/tattoo.git
   git push -u origin main
   ```
2. **Aktifkan Cloudinary di requirements.txt** (uncomment):
   ```
   cloudinary==1.44.1
   django-cloudinary-storage==0.3.1
   ```
   Push perubahan.
3. **Login ke [Vercel](https://vercel.com)** → **Add New Project** → Import GitHub repo
4. **Configure Project**:
   - Framework Preset: **Other**
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
   - Output Directory: kosongkan
   - Install Command: kosongkan (sudah di build command)
5. **Environment Variables** (Settings → Environment Variables):
   ```
   SECRET_KEY=<random-50-char>
   DEBUG=False
   ALLOWED_HOSTS=.vercel.app
   CSRF_TRUSTED_ORIGINS=https://your-project.vercel.app
   DATABASE_URL=postgres://user:pass@host:5432/db
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   ```
6. **Deploy** → tunggu sampai selesai
7. **Jalankan migration** (Vercel → Project → Settings → Functions → atau via CLI):
   ```bash
   npm i -g vercel
   vercel login
   vercel env pull .env.local
   python manage.py migrate
   vercel env push  # opsional
   ```
   Atau lebih mudah: tambah migration ke build command:
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
   ```
8. **Selesai!** App kamu live di `https://your-project.vercel.app`

> 💡 **Tips**: Karena Vercel serverless, `python manage.py createsuperuser` tidak bisa dijalankan langsung. Pakai ini:
> ```bash
> vercel exec --python manage.py createsuperuser
> ```
> Atau buat user via Django shell di environment lokal yang konek ke DATABASE_URL production.

---

<a name="custom-domain"></a>
## 4. Setup Custom Domain

### Di Hostinger

1. **Beli domain** di Hostinger (atau transfer dari registrar lain)
2. **Setup DNS** otomatis (jika domain di Hostinger)
3. **Point domain** ke folder hosting di hPanel → Domains → Pointers/Addon Domains

### Di Vercel

1. **Beli domain** di mana saja (Namecheap, Cloudflare, dll)
2. **Di Vercel Project** → Settings → Domains → Add
3. **Tambah domain** `yourdomain.com` dan `www.yourdomain.com`
4. **Update DNS** di registrar domain kamu:
   - Untuk **apex domain** (`yourdomain.com`):
     ```
     A    @    76.76.21.21
     ```
   - Untuk **www subdomain**:
     ```
     CNAME www  cname.vercel-dns.com
     ```
5. **Tunggu propagasi DNS** (5 menit - 48 jam, biasanya <30 menit)
6. **SSL otomatis** dari Vercel
7. **Update environment variables** di Vercel:
   ```
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,.vercel.app
   CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```
8. **Redeploy** project

### Di Cloudflare (jika pakai Cloudflare DNS)

1. **Add site** di Cloudflare → copy nameservers
2. **Update nameservers** di registrar domain
3. **DNS records** di Cloudflare:
   - `A @ 76.76.21.21` (proxy ON)
   - `CNAME www cname.vercel-dns.com` (proxy ON)
4. **SSL/TLS** di Cloudflare: set ke **Full** atau **Full (Strict)**

---

<a name="database"></a>
## 5. Setup Database Production

### PostgreSQL (Recommended untuk Vercel / Scalable)

**Neon (Free)**:
1. https://neon.tech → Signup → Create project
2. Copy connection string: `postgres://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require`
3. Set sebagai `DATABASE_URL`

**Supabase (Free)**:
1. https://supabase.com → New project
2. Settings → Database → Connection string (Transaction mode)
3. Format: `postgres://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`

### MySQL (untuk Hostinger / Shared hosting)

Format `DATABASE_URL`:
```
mysql://user:password@localhost:3306/dbname
```

Atau set langsung di settings (tidak disarankan — env var lebih portable):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dbname',
        'USER': 'user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### SQLite (Default - untuk dev / Hostinger kecil)

Tidak perlu setup apa-apa. File `db.sqlite3` akan dibuat otomatis.

⚠️ Jangan pakai SQLite di Vercel / serverless — filesystem tidak persistent!

---

<a name="media-storage"></a>
## 6. Setup Media Storage (untuk Serverless / Vercel)

Di Vercel, file `media/` akan hilang setiap redeploy. Wajib pakai external storage.

### Cloudinary (Recommended — Free 25GB)

1. Signup di https://cloudinary.com
2. Copy dari Dashboard:
   - Cloud Name
   - API Key
   - API Secret
3. Uncomment di `requirements.txt`:
   ```
   cloudinary==1.44.1
   django-cloudinary-storage==0.3.1
   ```
4. Set environment variables:
   ```
   CLOUDINARY_CLOUD_NAME=xxx
   CLOUDINARY_API_KEY=xxx
   CLOUDINARY_API_SECRET=xxx
   ```
5. **Otomatis terdeteksi** oleh `settings.py` — tidak perlu ubah kode!

### AWS S3 (Advanced)

1. Buat AWS account + S3 bucket
2. Install `django-storages[boto3]`
3. Set env vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`
4. Update `settings.py`:
   ```python
   if config('AWS_STORAGE_BUCKET_NAME', default=''):
       STORAGES = {
           'default': {'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage'},
           'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
       }
   ```

---

<a name="troubleshooting"></a>
## 7. Troubleshooting

### Error: "ALLOWED_HOSTS" / "Invalid HTTP_HOST"

Tambah domain kamu ke `ALLOWED_HOSTS`:
```
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Error: "CSRF verification failed"

Tambah URL lengkap ke `CSRF_TRUSTED_ORIGINS`:
```
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

### Error: Static files tidak muncul

1. Jalankan `python manage.py collectstatic --noinput`
2. Pastikan WhiteNoise di MIDDLEWARE
3. Cek `STATIC_ROOT` writable

### Error: Media uploads tidak muncul (Vercel)

- Pastikan `CLOUDINARY_*` env vars sudah di-set
- Cek di Cloudinary Dashboard apakah file terupload
- Cek `DEFAULT_FILE_STORAGE` di settings.py — harus `cloudinary_storage...`

### Error 500 di production

1. Set `DEBUG=False` → cek error log di dashboard hosting
2. Pastikan `ALLOWED_HOSTS` benar
3. Cek `requirements.txt` semua terinstall

### Database connection error

Cek `DATABASE_URL` format:
- PostgreSQL: `postgres://user:pass@host:5432/db`
- MySQL: `mysql://user:pass@host:3306/db`
- SQLite: kosongkan (default)

Pastikan IP server di-allow di database firewall (untuk Vercel: tambahkan `0.0.0.0/0` di Supabase/Neon).

### Performance lambat di Vercel

- Vercel serverless cold start bisa 1-3 detik
- Pakai Neon/Supabase connection pooling
- Cache static files di CDN Vercel (otomatis)

---

## Checklist Deploy Production

- [ ] `SECRET_KEY` di-generate baru (50+ char random)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` di-set dengan domain production
- [ ] `CSRF_TRUSTED_ORIGINS` di-set dengan `https://` URL
- [ ] Database production (PostgreSQL untuk Vercel)
- [ ] Cloudinary di-setup (untuk Vercel)
- [ ] `python manage.py migrate` sudah dijalankan
- [ ] `python manage.py collectstatic --noinput` sudah dijalankan
- [ ] `python manage.py createsuperuser` sudah dibuat
- [ ] SSL aktif (otomatis di Vercel, perlu setup di Hostinger)
- [ ] Custom domain sudah point + propagasi DNS selesai
- [ ] Test register, login, booking, payment end-to-end

---

# REST API (JSON)

Project ini punya **dua sisi** di satu Django project:
1. **Web HTML** di `/` (root) — untuk customer & artist via browser.
2. **REST API JSON** di `/api/v1/` — untuk integrasi, mobile app, atau frontend SPA terpisah.

Base URL (production): `https://yourdomain.com/api/v1/`
Base URL (development): `http://127.0.0.1:8000/api/v1/`

Dokumentasi interaktif (browsable API) tersedia di setiap endpoint saat `DEBUG=True`.

## Authentication

API pakai **Session Authentication** (login via web) + **Basic Authentication** (untuk script/testing).
Untuk mobile app production, tambahkan JWT (lihat catatan di bawah).

```bash
# Login untuk session
curl -c cookies.txt -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -d "username=john&password=secret"

# Pakai session untuk request selanjutnya
curl -b cookies.txt http://127.0.0.1:8000/api/v1/bookings/

# Atau pakai Basic Auth
curl -u john:secret http://127.0.0.1:8000/api/v1/bookings/
```

## Endpoints

### Public (no auth)

| Method | URL | Deskripsi |
|---|---|---|
| `GET` | `/api/v1/` | API root (links ke semua endpoints) |
| `GET` | `/api/v1/health/` | Health check (untuk monitoring) |
| `GET` | `/api/v1/categories/` | List kategori layanan |
| `GET` | `/api/v1/services/` | List services (pagination, filter, search) |
| `GET` | `/api/v1/services/<id>/` | Detail service + packages |
| `GET` | `/api/v1/services/<id>/packages/` | List packages untuk service tertentu |
| `GET` | `/api/v1/artists/` | List artist |
| `GET` | `/api/v1/artists/<id>/` | Detail artist + portfolio |
| `GET` | `/api/v1/artists/<id>/portfolio/` | Portfolio items |
| `GET` | `/api/v1/artists/<id>/reviews/` | Reviews untuk artist |
| `GET` | `/api/v1/payment-methods/` | 15 metode pembayaran (bank VA, e-wallet, QRIS, retail, credit card) |

### Authenticated

| Method | URL | Deskripsi |
|---|---|---|
| `GET` | `/api/v1/bookings/` | List booking milik user (atau semua jika staff) |
| `POST` | `/api/v1/bookings/` | Buat booking baru |
| `GET` | `/api/v1/bookings/<id>/` | Detail booking |
| `PATCH` | `/api/v1/bookings/<id>/` | Update (cancel via `{"status": "cancelled"}`) |
| `DELETE` | `/api/v1/bookings/<id>/` | Hapus booking (jika masih `pending`/`confirmed`) |
| `GET` | `/api/v1/bookings/<id>/payment-instructions/?method=<code>` | Ambil instruksi pembayaran (VA number, dll) |
| `POST` | `/api/v1/bookings/<id>/confirm-payment/` | Upload bukti + konfirmasi (SOP enforced) |
| `GET` | `/api/v1/reviews/` | List reviews |
| `POST` | `/api/v1/reviews/` | Buat review baru |

### Query params (filtering, search, ordering)

```bash
# Filter by category
GET /api/v1/services/?category=2

# Search by name
GET /api/v1/services/?search=tattoo

# Order by price
GET /api/v1/services/?ordering=price

# Combine: active services in category, ordered by price desc
GET /api/v1/services/?category=2&is_active=true&ordering=-price

# Pagination (default 20 per page)
GET /api/v1/services/?page=2
```

## Contoh Penggunaan

### 1. List services

```bash
curl http://127.0.0.1:8000/api/v1/services/
```

Response:
```json
{
  "count": 12,
  "next": "http://127.0.0.1:8000/api/v1/services/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Old School Tattoo",
      "short_desc": "Traditional American style",
      "price": "1200000.00",
      "price_label": "Mulai Rp 1.200.000",
      "duration": 120,
      "is_popular": true,
      "category": 2,
      "category_name": "Traditional",
      "image_url": "/media/services/old-school.jpg"
    }
  ]
}
```

### 2. Buat booking

```bash
curl -X POST http://127.0.0.1:8000/api/v1/bookings/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "service": 1,
    "artist": 3,
    "booking_date": "2026-07-01",
    "booking_time": "14:00:00",
    "mode": "studio",
    "location_address": "Jl. Test No. 123, Jakarta",
    "notes": "Tattoo lengan kiri"
  }'
```

Response (201):
```json
{
  "id": 42,
  "transaction_id": null,
  "user": 5,
  "user_username": "john",
  "artist": 3,
  "artist_nickname": "Budi",
  "service": 1,
  "service_name": "Old School Tattoo",
  "package": null,
  "mode": "studio",
  "mode_display": "Datang ke Studio",
  "status": "pending",
  "status_display": "Menunggu Konfirmasi",
  "booking_date": "2026-07-01",
  "booking_time": "14:00:00",
  "location_address": "Jl. Test No. 123, Jakarta",
  "total_price": "1200000.00",
  "travel_fee": "0.00",
  "is_paid": false,
  "paid_at": null,
  "payment_status": "unpaid",
  "payment_status_display": "Belum Dibayar",
  "payment_method": null,
  "verification_status": "not_required",
  "created_at": "2026-06-07T10:30:00Z"
}
```

### 3. Ambil instruksi pembayaran

```bash
curl -b cookies.txt \
  "http://127.0.0.1:8000/api/v1/bookings/42/payment-instructions/?method=bca_va"
```

Response (200):
```json
{
  "method": "bca_va",
  "method_label": "BCA Virtual Account",
  "method_logo": "/static/tattoo/img/payments/bca.svg",
  "group": "bank_va",
  "amount": 1200000,
  "transaction_id": "TRX-20260607-001",
  "booking_id": 42,
  "requires_proof": true,
  "expires_at": "2026-06-08T10:30:00Z",
  "type": "virtual_account",
  "bank_name": "BCA",
  "account_number": "8808-1234-5678",
  "account_name": "Bali Tattoo Studio",
  "instructions": "Transfer tepat hingga 3 digit unik..."
}
```

### 4. Konfirmasi + upload bukti (SOP)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/bookings/42/confirm-payment/ \
  -b cookies.txt \
  -F "method=bca_va" \
  -F "sop_agreement=1" \
  -F "customer_name=John Doe" \
  -F "customer_email=john@example.com" \
  -F "customer_phone=081234567890" \
  -F "payment_proof=@/path/to/bukti-transfer.jpg"
```

Response (200):
```json
{
  "detail": "Bukti pembayaran dikirim. Menunggu verifikasi artist.",
  "requires_verification": true,
  "booking": {
    "id": 42,
    "payment_status": "pending",
    "payment_status_display": "Menunggu Verifikasi",
    "verification_status": "pending",
    "payment_proof_url": "/media/payment_proofs/booking_42_proof.jpg"
  }
}
```

Error response jika SOP tidak dipatuhi (400):
```json
{
  "detail": "Bukti pembayaran wajib diupload untuk metode ini."
}
// atau
{
  "detail": "Wajib menyetujui pernyataan SOP (sop_agreement=1)."
}
```

## CORS (Cross-Origin)

Untuk akses dari frontend SPA / mobile web di domain berbeda, set di `.env`:

```env
# Pisahkan koma untuk multiple origins
CORS_ALLOWED_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com

# Regex untuk subdomain dinamis
CORS_ALLOWED_ORIGIN_REGEXES=^https://[a-z0-9-]+\.yourdomain\.com$

# Set True HANYA jika pakai session/cookie auth
CORS_ALLOW_CREDENTIALS=False
```

Tanpa konfigurasi, hanya same-origin yang diizinkan (aman untuk mobile app native yang tidak pakai browser).

## Mobile App

Untuk integrasi dengan mobile app:

1. **Android/iOS native**: tidak butuh CORS (bukan browser). Pakai Basic Auth atau tambahkan JWT.
2. **Flutter/React Native dengan WebView**: butuh CORS setup seperti di atas.
3. **PWA (Progressive Web App)**: butuh CORS + service worker config.

## Menambah JWT (opsional)

Default pakai Session + Basic Auth. Untuk JWT, install:
```bash
pip install djangorestframework-simplejwt
```

Tambah di `settings.py`:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}
```

Login: `POST /api/v1/auth/token/` dengan `{"username": "...", "password": "..."}` → return `access` + `refresh` token.
Refresh: `POST /api/v1/auth/token/refresh/` dengan `{"refresh": "..."}` → return new `access`.

## Legacy `/v1/` redirect

Jika client lama masih pakai `/v1/models`, `/v1/services`, dll, akan otomatis 301 redirect ke `/api/v1/...`. Update client untuk pakai prefix `/api/v1/`.

## Testing API

Test cepat dengan `curl` atau Postman. Browsable API di browser (saat `DEBUG=True`) juga bisa untuk eksplorasi endpoint.

```bash
# Health check
curl http://127.0.0.1:8000/api/v1/health/

# List services (first page)
curl http://127.0.0.1:8000/api/v1/services/

# Login + protected endpoint
curl -c /tmp/cookies -X POST http://127.0.0.1:8000/accounts/login/ \
  -d "username=apitest&password=testpass123"
curl -b /tmp/cookies http://127.0.0.1:8000/api/v1/bookings/
```

---

# Troubleshooting

## ERR_SSL_PROTOCOL_ERROR di `http://127.0.0.1:8000/`

**Penyebab:** Ada stale `runserver` process yang masih jalan dengan `DEBUG=False` (production mode). Process itu mengirim 301 ke `https://`, browser lalu coba HTTPS → SSL error karena tidak ada HTTPS server.

**Solusi:**
```powershell
# Kill semua Python process
Get-Process python | Stop-Process -Force

# Tunggu 5 detik, lalu start ulang
python manage.py runserver
```

Atau pakai port berbeda untuk runserver yang baru:
```powershell
python manage.py runserver 127.0.0.1:8001
```

**Prevention:** Pastikan `DEBUG=True` di `.env` untuk development. Default-nya sekarang sudah `True`, tapi kalau override di environment variable pastikan `DEBUG=True`.

## "DisallowedHost at /"

Tambahkan domain/IP ke `ALLOWED_HOSTS` di `.env`:
```env
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

## Static files 404 di production

```bash
python manage.py collectstatic --noinput
```

Pastikan `STATIC_ROOT` ada dan WhiteNoise configured. Cek juga `STATICFILES_STORAGE` di settings.

## Port 8000 sudah dipakai

```powershell
# Cari process di port 8000
Get-NetTCPConnection -LocalPort 8000 | Format-Table

# Kill
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Atau pakai port lain
python manage.py runserver 127.0.0.1:8080
```

## Migration error

```bash
# Lihat migration status
python manage.py showmigrations

# Apply migration
python manage.py migrate

# Reset DB (HATI-HATI: hapus semua data)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## API 404 / tidak ada endpoint

Pastikan prefix `/api/v1/` di URL. Contoh benar:
- `http://127.0.0.1:8000/api/v1/services/` ✓
- `http://127.0.0.1:8000/api/services/` ✗ (tanpa `v1`)

Lihat [section REST API](#rest-api-json) untuk daftar endpoint lengkap.

## CORS error di browser

Tambahkan origin frontend ke `.env`:
```env
CORS_ALLOWED_ORIGINS=https://app.yourdomain.com
```

Restart server setelah edit `.env`.

---

Butuh bantuan? Hubungi support di WhatsApp atau buat issue di GitHub repo.
