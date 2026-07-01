from decouple import config
from storages.backends.s3boto3 import S3Boto3Storage


class SupabaseStorageBucket2(S3Boto3Storage):
    bucket_name = config('SUPABASE_STORAGE_BUCKET_2', default='media-v2')
