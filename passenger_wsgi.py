"""
Hostinger entry point untuk Django via Phusion Passenger (cPanel).
File ini di-referensikan oleh .htaccess di public_html.

Setup di Hostinger:
1. Upload semua file project ke ~/domains/yourdomain.com/
2. Setup Python App di cPanel (Python Selector > Setup Application)
3. Application root: /home/user/domains/yourdomain.com
4. Application URL: /
5. Application startup file: passenger_wsgi.py
6. Application Entry point: application
7. Set environment variables di cPanel > Python > Environment variables
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bisnis.settings')

# Lazy import untuk performa
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
