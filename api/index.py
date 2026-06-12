"""
Vercel entry point untuk Django.
File ini di-referensikan oleh vercel.json sebagai handler untuk semua routes.
WhiteNoise (di MIDDLEWARE) akan serve static files secara otomatis.

PENTING untuk Vercel build: `application` HARUS di-assign di top-level module
(body AST level). Vercel static parser hanya cek `tree.body` (bukan nested di
try/except). Jadi kita pakai helper function + assign top-level.
"""

import os
import sys
import json
from pathlib import Path

# Pastikan project root ada di Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Set Django settings module SEBELUM import Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bisnis.settings')


def _get_env_snapshot():
    """Ambil snapshot env vars yang relevan (aman, tanpa password)."""
    keys = ['DATABASE_URL', 'DIRECT_URL', 'SECRET_KEY', 'DEBUG', 'VERCEL',
            'ALLOWED_HOSTS', 'CSRF_TRUSTED_ORIGINS', 'PYTHONUNBUFFERED',
            'DJANGO_SETTINGS_MODULE', 'SUPABASE_URL', 'SUPABASE_SERVICE_KEY',
            'SUPABASE_STORAGE_BUCKET', 'SUPABASE_REGION']
    snapshot = {}
    for k in keys:
        val = os.environ.get(k, '<NOT SET>')
        # Maskasi value sensitif
        if k in ('DATABASE_URL', 'DIRECT_URL', 'SECRET_KEY'):
            if val != '<NOT SET>':
                val = val[:20] + '...' + val[-4:] if len(val) > 30 else '***SET***'
        snapshot[k] = val
    # Tambahkan semua env var lain yang menarik
    other = {k: v for k, v in os.environ.items()
             if k.isupper() and k not in keys}
    snapshot['OTHER_ENV_VARS'] = other
    return snapshot


def _diagnose_app(environ, start_response):
    """WSGI app untuk /api/v1/diagnose/ — jalan tanpa Django."""
    import pprint
    snap = _get_env_snapshot()
    accept = environ.get('HTTP_ACCEPT', '')
    if 'text/html' in accept:
        body = '<html><body><h1>Env Diagnose</h1><pre>' + pprint.pformat(snap) + '</pre></body></html>'
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    else:
        body = json.dumps(snap, indent=2)
        start_response('200 OK', [('Content-Type', 'application/json')])
    return [body.encode('utf-8')]


# Intercept /api/v1/diagnose/ SEBELUM Django — biar tetap bisa diakses
# meskipun Django gagal start. Vercel WSGI memanggil application()
# setiap request, jadi kita handle routing manual di sini.
# Simpan reference ke diagnose app.
_DIAGNOSE_PATH = '/api/v1/diagnose/'


def _detect_hint(error_msg):
    """Deteksi jenis error dan return hint yang relevan."""
    if 'DATABASE_URL' in error_msg or 'Vercel filesystem' in error_msg:
        return (
            '<strong>Setup DATABASE_URL di Vercel (3 langkah):</strong><br><br>'
            '<strong>1.</strong> Login ke <a href="https://supabase.com/dashboard">Supabase</a> '
            '(atau <a href="https://console.neon.tech">Neon</a> / '
            '<a href="https://railway.app">Railway</a>) &rarr; buka project kamu<br><br>'
            '<strong>2.</strong> Pergi ke <strong>Project Settings &rarr; Database &rarr; Connection string &rarr; URI</strong><br>'
            'Copy connection string (format: <code>postgresql://postgres:PASSWORD@db.REF.supabase.co:5432/postgres</code>)<br>'
            'Tambahkan <code>?sslmode=require</code> di akhir URL<br><br>'
            '<strong>3.</strong> Vercel &rarr; Project &rarr; Settings &rarr; Environment Variables:<br>'
            '<div class="code">'
            'Key:   DATABASE_URL<br>'
            'Value: postgresql://postgres:YOUR_PASSWORD@db.YOUR_REF.supabase.co:5432/postgres?sslmode=require'
            '</div>'
            'Save &rarr; tab Deployments &rarr; klik titik tiga &rarr; <strong>Redeploy</strong><br><br>'
            '<strong>Catatan:</strong> URL <code>https://xxx.supabase.co/rest/v1/</code> adalah REST API, '
            'BUKAN database URL. Yang kamu butuhkan adalah PostgreSQL connection string dari '
            '<strong>Project Settings &rarr; Database</strong>.<br><br>'
            '<strong>Test koneksi lokal dulu (opsional):</strong><br>'
            '<div class="code">'
            'set DATABASE_URL=postgresql://postgres:PASSWORD@db.REF.supabase.co:5432/postgres?sslmode=require<br>'
            'python manage.py migrate<br>'
            'python manage.py runserver'
            '</div>'
            'Kalau local jalan &rarr; push ke Vercel & redeploy.<br><br>'
            'Cek status env vars: <a href="/api/v1/diagnose/">/api/v1/diagnose/</a>'
        )
    if 'psycopg' in error_msg.lower() or 'postgresql' in error_msg.lower():
        return (
            'Driver PostgreSQL belum terinstall atau DATABASE_URL salah format.<br>'
            'Pastikan <code>requirements.txt</code> ada baris: '
            '<code>psycopg[binary]==3.2.3</code><br>'
            'Pastikan DATABASE_URL format: '
            '<code>postgresql://user:pass@host:5432/db?sslmode=require</code><br><br>'
            'Cek status: <a href="/api/v1/diagnose/">/api/v1/diagnose/</a>'
        )
    if 'ALLOWED_HOSTS' in error_msg or 'DisallowedHost' in error_msg:
        return (
            'Domain tidak masuk ALLOWED_HOSTS. Default sudah include <code>.vercel.app</code>,<br>'
            'tapi kalau pakai custom domain tambahkan manual di env Vercel:<br>'
            '<div class="code">ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app,yourdomain.com</div><br>'
            'Cek status: <a href="/api/v1/diagnose/">/api/v1/diagnose/</a>'
        )
    if 'SECRET_KEY' in error_msg:
        return (
            'Set <code>SECRET_KEY</code> di Vercel project settings.<br>'
            'Generate baru:<br>'
            '<div class="code">python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"</div>'
            'Copy output &rarr; paste ke Vercel env var SECRET_KEY.<br><br>'
            'Cek status: <a href="/api/v1/diagnose/">/api/v1/diagnose/</a>'
        )
    return (
        'Cek Vercel logs untuk detail (Project &rarr; Logs). Kemungkinan:<br>'
        '&bull; Environment variable ada yang missing<br>'
        '&bull; Database tidak bisa dikonek (firewall / IP / wrong password)<br>'
        '&bull; requirements.txt konflik versi<br><br>'
        'Cek status env vars: <a href="/api/v1/diagnose/">/api/v1/diagnose/</a>'
    )


def _make_error_app(error_msg, hint):
    """Build a WSGI app that returns a helpful HTML/JSON error page."""
    snap = _get_env_snapshot()
    safetype = 'env-match' if snap.get('DATABASE_URL', '<NOT SET>') != '<NOT SET>' else 'env-missing'

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mohon Maaf - Bali Tattoo Studio</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          max-width: 780px; margin: 60px auto; padding: 20px; line-height: 1.6; color: #222; }}
  h1 {{ color: #c00; margin-bottom: 8px; }}
  h3 {{ margin-top: 24px; margin-bottom: 6px; }}
  .code {{ background: #f4f4f4; border-left: 4px solid #c00; padding: 12px 16px;
           border-radius: 4px; font-family: ui-monospace, "Cascadia Code", monospace;
           white-space: pre-wrap; word-break: break-word; font-size: 13px; }}
  .hint {{ background: #fff8e1; border-left: 4px solid #f0a000; padding: 12px 16px;
           border-radius: 4px; margin-top: 20px; }}
  .env-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13px; }}
  .env-table td {{ padding: 4px 8px; border-bottom: 1px solid #ddd; }}
  .env-table td:first-child {{ font-weight: bold; white-space: nowrap; }}
  .missing {{ color: #c00; font-weight: bold; }}
  .ok {{ color: #090; }}
  a {{ color: #0066cc; }}
</style>
</head>
<body>
<h1>Mohon Maaf</h1>
<p>Aplikasi belum bisa diakses karena konfigurasi belum lengkap. Tim kami akan segera menindaklanjuti.</p>
<h2>Error:</h2>
<div class="code">{error_msg}</div>
<div class="hint"><strong>Next step:</strong><br>{hint}</div>
<h3>Environment Variables (terbaca Vercel):</h3>
<table class="env-table">
"""
    for k, v in snap.items():
        if k == 'OTHER_ENV_VARS':
            continue
        css = 'missing' if v == '<NOT SET>' else 'ok'
        html += f'<tr><td>{k}</td><td class="{css}">{v}</td></tr>\n'

    html += """</table>
<p><a href="/api/v1/diagnose/">/api/v1/diagnose/</a> — detail lengkap</p>
<hr>
<p><small>Lihat <code>DEPLOYMENT.md</code> section "Setup Database (Vercel butuh PostgreSQL)" untuk langkah lengkap.</small></p>
</body>
</html>"""

    payload_dict = {'error': error_msg, 'hint_html': hint, 'status': 500, 'env': snap, 'safetype': safetype}

    def app(environ, start_response):
        accept = environ.get('HTTP_ACCEPT', '')
        is_browser = 'text/html' in accept
        if is_browser:
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
            return [html.encode('utf-8')]
        payload = json.dumps(payload_dict)
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [payload.encode('utf-8')]

    return app


def _load_application():
    """Load Django WSGI app; kalau gagal return error app dengan route diagnose."""
    try:
        from django.core.wsgi import get_wsgi_application
        django_app = get_wsgi_application()
        return django_app
    except Exception as exc:
        err = str(exc) or type(exc).__name__
        error_app = _make_error_app(err, _detect_hint(err))

        # Bungkus agar /api/v1/diagnose/ tetap bisa diakses
        def _wrapped_app(environ, start_response):
            path = environ.get('PATH_INFO', '')
            if path == _DIAGNOSE_PATH:
                return _diagnose_app(environ, start_response)
            return error_app(environ, start_response)

        return _wrapped_app


# ============================================================
# `application` di TOP-LEVEL (tree.body) — required oleh Vercel parser
# ============================================================
application = _load_application()
