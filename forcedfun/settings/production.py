import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import os

from .common import *  # noqa: F403

sentry_sdk.init(
    environment=os.getenv("ENVIRONMENT"),
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
)

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
