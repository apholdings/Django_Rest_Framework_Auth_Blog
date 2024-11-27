from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    location = "static"
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN


class PublicMediaStorage(S3Boto3Storage):
    location = 'media'  # Define la carpeta principal para los archivos de medios
    default_acl = 'public-read'  # Permitir acceso público a los archivos
    file_overwrite = False  # Evitar sobrescribir archivos con el mismo nombre