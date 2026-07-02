import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bisnis'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'bisnis.settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
import django
django.setup()
from django.db import connection
with connection.cursor() as cur:
    for table in ['tattoo_service', 'tattoo_servicepackage', 'tattoo_artist']:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cur.fetchone()[0]
            print(f'{table}: {count} rows')
        except Exception as e:
            print(f'{table}: ERROR - {e}')
