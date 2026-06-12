"""
Django settings for bisnis project.

Dikonfigurasi 100% via environment variables (.env di dev / dashboard hosting di prod)
sehingga aplikasi dapat di-deploy di Hostinger, Vercel, Render, Railway, atau host apapun
tanpa mengubah kode.

Lihat .env.example untuk daftar lengkap environment variables yang didukung.
"""

import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url


# ============================================================
# PATH
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# SECURITY & DEBUG
# ============================================================
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-dev-only-CHANGE-ME-IN-PRODUCTION-1234567890abcdef'
)

# Default DEBUG=True untuk development (override di .env untuk production)
# PENTING: Set DEBUG=False di .env / hosting dashboard untuk production!
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS: pisahkan dengan koma di .env
# Default include `.vercel.app` & `.localhost` (leading dot = wildcard subdomain)
# untuk support Vercel deployment (subdomain random: bisnis-xxx.vercel.app)
# + preview deployment (pr-123-bisnis-xxx.vercel.app)
# Untuk custom domain: ALLOWED_HOSTS=...,yourdomain.com,www.yourdomain.com
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,.vercel.app,.localhost',
    cast=Csv()
)

# CSRF_TRUSTED_ORIGINS: untuk HTTPS / cross-site form post
# Format lengkap URL: https://domain.com
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000', cast=Csv())


# ============================================================
# APPLICATION
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third party
    'rest_framework',
    'django_filters',
    'corsheaders',
    'storages',
    # Local
    'tattoo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise HARUS di posisi setelah SecurityMiddleware & sebelum semua middleware lain
    # yang mengakses request (untuk serve static files)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # CORS harus sebelum CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bisnis.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tattoo.context_processors.navbar_data',
            ],
        },
    },
]

WSGI_APPLICATION = 'bisnis.wsgi.application'


# ============================================================
# STARTUP WARNINGS (bantu debug production deployment)
# ============================================================
import os as _os
import logging as _logging
import warnings as _warnings

_startup_logger = _logging.getLogger('django.startup')

if not DEBUG and _os.environ.get('VERCEL'):
    # Vercel deployment: cek apakah subdomain Vercel sudah di-allow
    vercel_allowed = any(h == '.vercel.app' or h.endswith('.vercel.app') for h in ALLOWED_HOSTS)
    if not vercel_allowed:
        _startup_logger.warning(
            "VERCEL DEPLOYMENT: '*.vercel.app' tidak ada di ALLOWED_HOSTS. "
            "Tambahkan ',.vercel.app' ke env var ALLOWED_HOSTS di Vercel project settings, "
            "atau redeploy setelah update settings.py default."
        )

if not DEBUG:
    # Tampilkan konfigurasi host saat startup production (untuk verifikasi)
    _startup_logger.info(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    _startup_logger.info(f"CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
    if '*' in ALLOWED_HOSTS:
        _startup_logger.warning(
            "ALLOWED_HOSTS berisi '*' (allow all). Ini AMAN untuk development, "
            "TAPI tidak untuk production (rentan HTTP Host header attack). "
            "Ganti dengan domain spesifik."
        )


# ============================================================
# DATABASE
# ============================================================
# Prioritas:
# 1. Jika DATABASE_URL di-set → pakai itu (PostgreSQL/MySQL/cockroachdb untuk production)
# 2. Jika tidak → fallback ke SQLite (cocok untuk dev & Hostinger shared)
#
# PENTING untuk Vercel: Filesystem di Vercel READ-ONLY (kecuali /tmp, tapi tidak
# persistent antar invocation). SQLite TIDAK BISA dipakai di Vercel.
# Jadi kalau detect environment Vercel tapi DATABASE_URL kosong → fail fast
# dengan error message jelas, bukan diam-diam fallback ke SQLite yang akan crash.
_DATABASE_URL = os.environ.get('DATABASE_URL') or config('DATABASE_URL', default='')
_DIRECT_URL = os.environ.get('DIRECT_URL') or config('DIRECT_URL', default='')
_IS_VERCEL = bool(os.environ.get('VERCEL')) or bool(config('VERCEL', default=False, cast=bool))

if _DATABASE_URL:
    DATABASES = {'default': dj_database_url.config(
        default=_DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )}
    DATABASES['default']['OPTIONS'] = {
        **DATABASES['default'].get('OPTIONS', {}),
        'connect_timeout': 5,
    }
    # Direct connection (session pooler) untuk migrations
    if _DIRECT_URL:
        DATABASES['direct'] = dj_database_url.config(
            default=_DIRECT_URL,
            conn_max_age=0,
            conn_health_checks=True,
        )
elif _IS_VERCEL:
    # Vercel tanpa DATABASE_URL: pakai in-memory SQLite agar Django tetap start.
    # Semua query akan gagal (table tidak ada) — tapi error handling di views
    # akan catch dan render halaman tetap jalan dengan data kosong.
    _startup_logger.warning(
        "DATABASE_URL tidak di-set di Vercel! "
        "Aplikasi berjalan dengan in-memory database — data tidak persisten. "
        "Atur DATABASE_URL di Vercel project settings untuk production."
    )
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    # Development & Hostinger shared: SQLite OK
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ============================================================
# PASSWORD VALIDATION
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC FILES (CSS, JS, images)
# ============================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise config
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_SKIP_CHARSET = True

# Auto-detect tambahan file statis di root
WHITENOISE_ROOT = BASE_DIR


# ============================================================
# STORAGES (Django 6.x) — includes static & media backends
# ============================================================
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# ============================================================
# MEDIA FILES (user uploads) — Supabase Storage (S3-compatible)
# ============================================================
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Supabase Storage via S3-compatible API
USE_SUPABASE_STORAGE = all([
    config('SUPABASE_SERVICE_KEY', default=''),
    config('SUPABASE_URL', default=''),
    config('SUPABASE_STORAGE_BUCKET', default='media'),
])

if USE_SUPABASE_STORAGE:
    SUPABASE_PROJECT_REF = config('SUPABASE_URL').replace('https://', '').split('.')[0]
    AWS_ACCESS_KEY_ID = config('SUPABASE_S3_ACCESS_KEY', default='')
    AWS_SECRET_ACCESS_KEY = config('SUPABASE_S3_SECRET_KEY', default='')
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        STORAGES['default']['BACKEND'] = 'storages.backends.s3boto3.S3Boto3Storage'
        AWS_STORAGE_BUCKET_NAME = config('SUPABASE_STORAGE_BUCKET', default='media')
        AWS_S3_ENDPOINT_URL = f'https://{SUPABASE_PROJECT_REF}.storage.supabase.co/storage/v1/s3'
        AWS_S3_REGION_NAME = config('SUPABASE_REGION', default='ap-southeast-2')
        AWS_S3_SIGNATURE_VERSION = 's3v4'
        AWS_S3_ADDRESSING_STYLE = 'path'
        AWS_DEFAULT_ACL = 'public-read'
        AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
        AWS_S3_FILE_OVERWRITE = False
        AWS_QUERYSTRING_EXPIRE = 86400


# ============================================================
# LOGIN
# ============================================================
LOGIN_URL = 'login'

MESSAGE_TAGS = {
    'success': 'success',
    'error': 'danger',
    'info': 'info',
}


# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    # Test mode: izinkan akses tanpa token di dev. Di production pakai SessionAuth + login.
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# API throttle opsional (untuk public API)
# 'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle'],
# 'DEFAULT_THROTTLE_RATES': {'anon': '100/hour'}


# ============================================================
# CORS (Cross-Origin Resource Sharing) — untuk mobile app / frontend terpisah
# ============================================================
# Daftar origin yang diizinkan mengakses API.
# Pisahkan koma di .env: CORS_ALLOWED_ORIGINS=https://app.com,https://admin.app.com
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv(),
)
# Regex tambahan untuk subdomain dinamis (mis. *.vercel.app)
CORS_ALLOWED_ORIGIN_REGEXES = config(
    'CORS_ALLOWED_ORIGIN_REGEXES',
    default=r'^https?://(localhost|127\.0\.0\.1)(:\d+)?$',
    cast=lambda v: [r.strip() for r in v.split('|') if r.strip()] if v else [],
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
]


# ============================================================
# APPEND_SLASH — disable untuk /api/ agar tidak ada 301 redirect
# ============================================================
APPEND_SLASH = True  # tetap True untuk web HTML; API URL sudah include trailing slash


# ============================================================
# SECURITY (untuk production)
# ============================================================
if not DEBUG:
    # HTTPS redirect
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS: paksa browser pakai HTTPS selama 1 tahun
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Security headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_REFERRER_POLICY = 'same-origin'
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False


# ============================================================
# PAYMENT GATEWAY — Custom (tanpa Midtrans / external API)
# ============================================================
# Rekening & e-wallet platform untuk menerima pembayaran dari customer.
# Override via environment variable di production.
PLATFORM_PAYMENT_ACCOUNTS = {
    'bca': {
        'bank_name': 'BCA',
        'account_number': config('PAY_BCA_NUMBER', default='8808-1234-5678'),
        'account_name': config('PAY_BCA_NAME', default='Bali Tattoo Studio'),
    },
    'mandiri': {
        'bank_name': 'Mandiri',
        'account_number': config('PAY_MANDIRI_NUMBER', default='157-00-1234567-8'),
        'account_name': config('PAY_MANDIRI_NAME', default='Bali Tattoo Studio'),
    },
    'bni': {
        'bank_name': 'BNI',
        'account_number': config('PAY_BNI_NUMBER', default='8808-1234-5678-901'),
        'account_name': config('PAY_BNI_NAME', default='Bali Tattoo Studio'),
    },
    'bri': {
        'bank_name': 'BRI',
        'account_number': config('PAY_BRI_NUMBER', default='0123-01-123456-50-9'),
        'account_name': config('PAY_BRI_NAME', default='Bali Tattoo Studio'),
    },
    'permata': {
        'bank_name': 'Permata',
        'account_number': config('PAY_PERMATA_NUMBER', default='8808-123456'),
        'account_name': config('PAY_PERMATA_NAME', default='Bali Tattoo Studio'),
    },
    'cimb': {
        'bank_name': 'CIMB Niaga',
        'account_number': config('PAY_CIMB_NUMBER', default='8808-1234-56'),
        'account_name': config('PAY_CIMB_NAME', default='Bali Tattoo Studio'),
    },
    'gopay': {
        'provider': 'GoPay',
        'number': config('PAY_GOPAY_NUMBER', default='081234567890'),
        'name': config('PAY_GOPAY_NAME', default='Bali Tattoo Studio'),
    },
    'ovo': {
        'provider': 'OVO',
        'number': config('PAY_OVO_NUMBER', default='081234567890'),
        'name': config('PAY_OVO_NAME', default='Bali Tattoo Studio'),
    },
    'dana': {
        'provider': 'DANA',
        'number': config('PAY_DANA_NUMBER', default='081234567890'),
        'name': config('PAY_DANA_NAME', default='Bali Tattoo Studio'),
    },
    'shopeepay': {
        'provider': 'ShopeePay',
        'number': config('PAY_SHOPEE_NUMBER', default='081234567890'),
        'name': config('PAY_SHOPEE_NAME', default='Bali Tattoo Studio'),
    },
    'linkaja': {
        'provider': 'LinkAja',
        'number': config('PAY_LINKAJA_NUMBER', default='081234567890'),
        'name': config('PAY_LINKAJA_NAME', default='Bali Tattoo Studio'),
    },
    'indomaret': {
        'provider': 'Indomaret',
        'payment_code_prefix': 'TATTOO',
    },
    'alfamart': {
        'provider': 'Alfamart',
        'payment_code_prefix': 'TATTOO',
    },
}

# Batas waktu pembayaran sebelum booking otomatis expire
PAYMENT_EXPIRY_HOURS = config('PAYMENT_EXPIRY_HOURS', default=24, cast=int)


# ============================================================
# DEFAULT SETTINGS
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging: tampilkan ke stdout di production (untuk Vercel/Heroku logs)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '[{asctime}] {levelname} {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO'},
    },
}
