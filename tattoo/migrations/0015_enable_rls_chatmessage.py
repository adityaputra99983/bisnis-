from django.db import migrations, connection


def forwards_sql(apps, schema_editor):
    if connection.vendor == 'postgresql':
        schema_editor.execute("ALTER TABLE public.tattoo_chatmessage ENABLE ROW LEVEL SECURITY;")
        schema_editor.execute("""
            CREATE POLICY chat_app_access ON public.tattoo_chatmessage
                FOR ALL
                USING (true)
                WITH CHECK (true);
        """)


def reverse_sql(apps, schema_editor):
    if connection.vendor == 'postgresql':
        schema_editor.execute("DROP POLICY IF EXISTS chat_app_access ON public.tattoo_chatmessage;")
        schema_editor.execute("ALTER TABLE public.tattoo_chatmessage DISABLE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):

    dependencies = [
        ('tattoo', '0014_fix_duplicate_payment_status_index'),
    ]

    operations = [
        migrations.RunPython(forwards_sql, reverse_sql, elidable=True),
    ]
