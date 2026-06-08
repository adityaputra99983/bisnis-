import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bisnis.settings')

import django
django.setup()

from django.db import connection

c = connection.cursor()
c.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
""")
tables = [r[0] for r in c.fetchall()]

for tbl in tables:
    c.execute(f'DROP POLICY IF EXISTS p_all_access ON public."{tbl}"')
    c.execute(f'ALTER TABLE public."{tbl}" DISABLE ROW LEVEL SECURITY')
    print(f'  OK  {tbl}')

print(f'\nRLS disabled on {len(tables)} tables.')
