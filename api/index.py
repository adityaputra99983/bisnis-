"""
Vercel entry point untuk Django.
File ini di-referensikan oleh vercel.json sebagai handler untuk semua routes.
WhiteNoise (di MIDDLEWARE) akan serve static files secara otomatis.
"""

import os
import sys
from pathlib import Path

# Pastikan project root ada di Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bisnis.settings')

# Lazy-load Django WSGI app agar Vercel cold start lebih cepat
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
