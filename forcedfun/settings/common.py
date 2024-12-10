import os
from pathlib import Path

from django.urls import reverse_lazy

from .utils import getbool
import dj_database_url

ALLOWED_HOSTS = ["*"]

PACKAGE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = PACKAGE_DIR.parent

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgres://forcedfun:@localhost:5432/forcedfun"
)
DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=500)}

DEBUG = getbool("DEBUG", False)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.sessions",
    "forcedfun",
    "django_extensions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "forcedfun.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "forcedfun.urls"

SECRET_KEY = os.getenv("SECRET_KEY", "not-so-secret-key")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PACKAGE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
]

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = Path(REPO_DIR, "staticfiles")

COMMIT = os.getenv("COMMIT", "local")

MEDIA_ROOT = Path(REPO_DIR, "media")

LOGIN_URL = reverse_lazy("login")
LOGIN_REDIRECT_URL = reverse_lazy("index")
LOGOUT_REDIRECT_URL = reverse_lazy("login")

import django_stubs_ext

django_stubs_ext.monkeypatch()

# https://docs.djangoproject.com/en/5.1/ref/settings/#csrf-trusted-origins
CSRF_TRUSTED_ORIGINS = [
    "https://*.ondigitalocean.app",
]
