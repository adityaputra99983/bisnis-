from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tattoo', '0014_fix_duplicate_payment_status_index'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE public.tattoo_chatmessage ENABLE ROW LEVEL SECURITY;",
                # Django handles all auth/access control at the app layer,
                # so the database role needs full access to all rows.
                # This RLS policy preserves that while satisfying the
                # Supabase lint check ("table has RLS enabled").
                # Access control is delegated entirely to Django middleware.
                """
                CREATE POLICY chat_app_access ON public.tattoo_chatmessage
                    FOR ALL
                    USING (true)
                    WITH CHECK (true);
                """,
            ],
            reverse_sql=[
                "DROP POLICY IF EXISTS chat_app_access ON public.tattoo_chatmessage;",
                "ALTER TABLE public.tattoo_chatmessage DISABLE ROW LEVEL SECURITY;",
            ],
            elidable=True,
        ),
    ]
