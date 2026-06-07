"""
URL Configuration untuk bisnis project.

Tersedia 2 "sisi" yang terkait:
1. WEB HTML  → /  (root)        — untuk browser / customer-facing
2. REST API  → /api/v1/...      — untuk mobile app / integrasi JSON

Di development: Django dev server serve static & media langsung.
Di production: WhiteNoise serve static files. Media files di-handle oleh
Cloudinary (jika env di-set) atau di-disable access langsung (pakai reverse proxy).

Untuk Hostinger dengan Apache + mod_wsgi / Passenger, lihat DEPLOYMENT.md.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponsePermanentRedirect


urlpatterns = [
    path('admin/', admin.site.urls),

    # ===== WEB HTML (customer + artist panel) =====
    path('', include('tattoo.urls')),

    # ===== REST API (JSON) =====
    path('api/v1/', include('tattoo.api.urls')),
]

# ============================================================
# Legacy /v1/ routes — fix 301 redirect untuk /v1/...
# Mengarahkan ke /api/v1/... agar tidak ada 301 dari APPEND_SLASH
# ============================================================
def _legacy_v1_redirect(request, path=''):
    """Redirect /v1/<path> → /api/v1/<path> (preserve trailing slash)."""
    new_path = f'/api/v1/{path}'
    if not new_path.endswith('/') and request.path.endswith('/'):
        new_path += '/'
    return HttpResponsePermanentRedirect(new_path)


urlpatterns += [
    re_path(r'^v1/(?P<path>.*)$', _legacy_v1_redirect),
]


# ============================================================
# STATIC & MEDIA FILES
# ============================================================
# WhiteNoise (di MIDDLEWARE) sudah handle static files di production.
# Hanya tambah URL patterns untuk:
# 1. Media files di development (DEBUG=True)
# 2. Media files di production KALAU pakai local storage (Hostinger) - di belakang reverse proxy
if settings.DEBUG:
    # Development: serve media via Django
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # WhiteNoise dev server juga handle static, tapi tambahkan ini untuk fallback
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
elif not getattr(settings, 'USE_CLOUDINARY', False):
    # Production dengan local media (Hostinger) - biasanya di-handle Apache .htaccess
    # Tambah ini sebagai fallback jika tidak ada reverse proxy
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ============================================================
# CUSTOM ERROR HANDLERS
# ============================================================
handler404 = 'tattoo.views.custom_404'
handler500 = 'tattoo.views.custom_500'
