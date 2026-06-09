import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):
    help = 'Migrate existing local media files to Supabase Storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually uploading',
        )
        parser.add_argument(
            '--model',
            default=None,
            help='Only migrate files for a specific model (e.g. tattoo.Service)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_model = options['model']

        if not settings.USE_SUPABASE_STORAGE:
            self.stdout.write(self.style.WARNING(
                'USE_SUPABASE_STORAGE is False. '
                'Make sure SUPABASE_URL, SUPABASE_SERVICE_KEY, '
                'and SUPABASE_STORAGE_BUCKET are set in .env'
            ))
            return

        is_s3 = getattr(settings, 'AWS_ACCESS_KEY_ID', False)
        if not is_s3:
            self.stdout.write(self.style.WARNING(
                'S3 credentials not configured. '
                'Set SUPABASE_S3_ACCESS_KEY and SUPABASE_S3_SECRET_KEY in .env'
            ))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no files will be uploaded\n'))

        # Find all image/file fields in the project
        models_with_files = self._get_file_models()

        if only_model:
            models_with_files = [
                m for m in models_with_files
                if f'{m[0].__module__}.{m[0].__name__}' == only_model
                or f'{m[0]._meta.app_label}.{m[0]._meta.model_name}' == only_model.lower()
            ]

        total_migrated = 0
        total_skipped = 0
        total_errors = 0

        for model_class, field_name in models_with_files:
            model_name = f'{model_class._meta.app_label}.{model_class._meta.model_name}.{field_name}'
            self.stdout.write(f'\n[{model_name}]')

            field = model_class._meta.get_field(field_name)
            queryset = model_class.objects.all()

            for obj in queryset:
                file_field = getattr(obj, field_name)
                if not file_field or not file_field.name:
                    continue

                local_path = Path(settings.MEDIA_ROOT) / file_field.name
                if not local_path.exists():
                    total_skipped += 1
                    self.stdout.write(f'  SKIP  {file_field.name} (file not found on disk)')
                    continue

                if file_field.storage.exists(file_field.name):
                    total_skipped += 1
                    self.stdout.write(f'  OK    {file_field.name} (already in storage)')
                    continue

                total_migrated += 1
                if dry_run:
                    self.stdout.write(f'  WOULD MIGRATE  {file_field.name}')
                    continue

                try:
                    with open(local_path, 'rb') as f:
                        content = f.read()

                    saved_name = file_field.save(file_field.name, ContentFile(content), save=False)
                    model_class.objects.filter(pk=obj.pk).update(**{field_name: saved_name})
                    self.stdout.write(f'  OK    {file_field.name}')
                except Exception as e:
                    total_errors += 1
                    self.stdout.write(self.style.ERROR(
                        f'  FAIL  {file_field.name}: {e}'
                    ))

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(f'Total migrated: {total_migrated}')
        self.stdout.write(f'Total skipped:  {total_skipped}')
        self.stdout.write(f'Total errors:   {total_errors}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\nRun without --dry-run to perform the migration'
            ))

    def _get_file_models(self):
        from django.db.models import ImageField, FileField

        result = []
        for model_class in apps.get_models():
            for field in model_class._meta.fields:
                if isinstance(field, (ImageField, FileField)):
                    result.append((model_class, field.name))
        return result
