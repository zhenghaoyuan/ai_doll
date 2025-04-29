from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import FileSystemStorage, Storage
from typing import Type


def get_media_storage(field=None) -> Storage:
    if settings.USE_S3:
        return PublicMediaStorage()
    else:
        return FileSystemStorage()


class StaticStorage(S3Boto3Storage):
    location = "static"
    default_acl = "public-read"

    def __init__(self, *args, **kwargs) -> None:
        kwargs["custom_domain"] = settings.AWS_CLOUDFRONT_DOMAIN
        super(StaticStorage, self).__init__(*args, **kwargs)


class PublicMediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = "public-read"
    file_overwrite = False

    def __init__(self, *args, **kwargs) -> None:
        kwargs["custom_domain"] = settings.AWS_CLOUDFRONT_DOMAIN
        super(PublicMediaStorage, self).__init__(*args, **kwargs)
