import os

from botocore.exceptions import ClientError
from django.utils.text import slugify
from storages.backends.s3boto3 import S3Boto3Storage


class SupabaseStorage(S3Boto3Storage):
    def exists(self, name):
        try:
            return super().exists(name)
        except ClientError as err:
            if err.response["ResponseMetadata"]["HTTPStatusCode"] in (400, 404):
                return False
            raise

    def _save(self, name, content):
        name = self._sanitize_name(name)
        return super()._save(name, content)

    def get_available_name(self, name, max_length=None):
        name = self._sanitize_name(name)
        return super().get_available_name(name, max_length)

    @staticmethod
    def _sanitize_name(name):
        dir_name, file_name = os.path.split(name.replace("\\", "/"))
        root, ext = os.path.splitext(file_name)
        safe_root = slugify(root) or "file"
        safe_name = safe_root + ext
        if dir_name:
            safe_name = dir_name + "/" + safe_name
        return safe_name
