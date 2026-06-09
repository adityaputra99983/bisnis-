import json
import urllib.request
import urllib.error
from django.core.management.base import BaseCommand, CommandError
from decouple import config


class Command(BaseCommand):
    help = 'Setup Supabase Storage bucket for media files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bucket',
            default=None,
            help='Bucket name (default: from SUPABASE_STORAGE_BUCKET env)',
        )

    def handle(self, *args, **options):
        bucket_name = options['bucket'] or config('SUPABASE_STORAGE_BUCKET', default='media')
        supabase_url = config('SUPABASE_URL', default='')
        service_key = config('SUPABASE_SERVICE_KEY', default='')

        if not supabase_url or not service_key:
            raise CommandError(
                'SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env'
            )

        api_url = f'{supabase_url}/storage/v1/bucket'
        headers = {
            'Authorization': f'Bearer {service_key}',
            'Content-Type': 'application/json',
            'apikey': service_key,
        }

        # 1. Check if bucket exists
        self.stdout.write(f'Checking bucket "{bucket_name}"...')
        try:
            req = urllib.request.Request(
                f'{api_url}/{bucket_name}',
                headers=headers,
                method='GET',
            )
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                self.stdout.write(self.style.SUCCESS(
                    f'Bucket "{bucket_name}" already exists (id: {data.get("id")})'
                ))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.stdout.write(f'Bucket "{bucket_name}" not found. Creating...')
                self._create_bucket(api_url, headers, bucket_name)
            elif e.code == 400:
                body = json.loads(e.read().decode())
                if 'already exists' in body.get('error', ''):
                    self.stdout.write(self.style.SUCCESS(
                        f'Bucket "{bucket_name}" already exists'
                    ))
                else:
                    raise CommandError(f'Error checking bucket: {body}')
            else:
                raise CommandError(f'HTTP {e.code}: {e.reason}')

        # 2. Make bucket public
        self.stdout.write('Setting bucket to public...')
        self._set_bucket_public(api_url, headers, bucket_name)

        # 3. Set CORS (optional for S3)
        self.stdout.write('Configuring CORS...')
        self._set_cors(api_url, bucket_name, headers)

        self.stdout.write(self.style.SUCCESS(
            f'\nSupabase Storage is ready!\n'
            f'  Bucket: {bucket_name}\n'
            f'  Endpoint: {config("SUPABASE_URL")}/storage/v1/s3\n'
            f'  Region: {config("SUPABASE_REGION", default="ap-southeast-2")}'
        ))

    def _create_bucket(self, api_url, headers, bucket_name):
        payload = json.dumps({
            'name': bucket_name,
            'public': True,
            'file_size_limit': 52428800,  # 50MB
            'allowed_mime_types': [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'image/svg+xml', 'application/pdf',
                'video/mp4', 'video/quicktime',
            ],
        }).encode()
        req = urllib.request.Request(
            api_url, data=payload, headers=headers, method='POST',
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                self.stdout.write(self.style.SUCCESS(
                    f'Bucket "{bucket_name}" created (id: {data.get("id")})'
                ))
        except urllib.error.HTTPError as e:
            body = json.loads(e.read().decode())
            raise CommandError(f'Failed to create bucket: {body}')

    def _set_bucket_public(self, api_url, headers, bucket_name):
        payload = json.dumps({
            'public': True,
        }).encode()
        req = urllib.request.Request(
            f'{api_url}/{bucket_name}',
            data=payload,
            headers=headers,
            method='PUT',
        )
        try:
            with urllib.request.urlopen(req) as resp:
                self.stdout.write(self.style.SUCCESS(
                    f'Bucket "{bucket_name}" set to public'
                ))
        except urllib.error.HTTPError as e:
            body = json.loads(e.read().decode())
            self.stdout.write(self.style.WARNING(
                f'Could not set bucket to public: {body}'
            ))

    def _set_cors(self, api_url, bucket_name, headers):
        cors_config = {
            'origins': ['*'],
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'HEAD'],
            'allowedHeaders': ['*'],
            'exposedHeaders': ['Content-Type', 'x-amz-*'],
            'maxAgeSeconds': 3600,
        }
        payload = json.dumps(cors_config).encode()
        req = urllib.request.Request(
            f'{api_url}/{bucket_name}/cors',
            data=payload,
            headers=headers,
            method='POST',
        )
        try:
            with urllib.request.urlopen(req) as resp:
                self.stdout.write(self.style.SUCCESS('CORS configured'))
        except urllib.error.HTTPError as e:
            body = json.loads(e.read().decode())
            self.stdout.write(self.style.WARNING(
                f'CORS config skipped: {body.get("error", e.reason)}'
            ))
