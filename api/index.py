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
    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Setup Required - 500</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          max-width: 720px; margin: 60px auto; padding: 20px; line-height: 1.6; color: #222; }}
  h1 {{ color: #c00; margin-bottom: 8px; }}
  .code {{ background: #f4f4f4; border-left: 4px solid #c00; padding: 12px 16px;
           border-radius: 4px; font-family: ui-monospace, "Cascadia Code", monospace;
           white-space: pre-wrap; word-break: break-word; }}
  .hint {{ background: #fff8e1; border-left: 4px solid #f0a000; padding: 12px 16px;
           border-radius: 4px; margin-top: 20px; }}
  a {{ color: #0066cc; }}
</style>
</head>
<body>
<h1>Setup Required (500)</h1>
<p>Aplikasi belum bisa start di Vercel karena konfigurasi belum lengkap.</p>
<h2>Error:</h2>
<div class="code">{error_msg}</div>
<div class="hint"><strong>Next step:</strong><br>{hint}</div>
<hr>
<p><small>Lihat <code>DEPLOYMENT.md</code> section "Setup Database (Vercel butuh PostgreSQL)" untuk langkah lengkap.</small></p>
</body>
</html>"""

    def app(environ, start_response):
        accept = environ.get('HTTP_ACCEPT', '')
        is_browser = 'text/html' in accept
        if is_browser:
            start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/html; charset=utf-8')])
            return [html.encode('utf-8')]
        payload = json.dumps({'error': error_msg, 'hint_html': hint, 'status': 500})
        start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'application/json')])
        return [payload.encode('utf-8')]

    return app


def _load_application():
    """Load Django WSGI app; return error WSGI app kalau gagal."""
    try:
        from django.core.wsgi import get_wsgi_application
        return get_wsgi_application()
    except Exception as exc:
        err = str(exc) or type(exc).__name__
        return _make_error_app(err, _detect_hint(err))


# ============================================================
# `application` di TOP-LEVEL (tree.body) — required oleh Vercel parser
# ============================================================
application = _load_application()
