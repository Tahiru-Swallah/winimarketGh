from .base import *
from decouple import config
from storages.backends.gcloud import GoogleCloudStorage

DEBUG = False

ADMINS = [
    ("winimarket Gh", "winimarketgh@gmail.com"),
    ("Suwa Gh", "suwagh724@gmail.com")
]

ALLOWED_HOSTS = ["*"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='').strip(),
        'USER': config('POSTGRES_USER', default='').strip(),
        'PASSWORD': config('POSTGRES_PASSWORD', default='').strip(),
        'HOST': config('DB_HOST', default='/cloudsql/steam-talent-484711-m9:us-east1:winimarket-db'),  # db for local compose
        'PORT': config('DB_PORT', default=5432, cast=int),
    }
}

SITE_URL = "https://winimarket-27948306085.us-east1.run.app"

# Max size (in bytes)
# Example: 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 * 1024 * 1024

# File upload limit (for FILES dict)
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB

SECURE_COOKIE = config('SECURE_COOKIE', default=True, cast=bool)

CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True  
SECURE_SSL_REDIRECT = True

SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Keep session alive for 6 months
SESSION_COOKIE_AGE = 60 * 60 * 24 * 180  # 6 months

SESSION_SAVE_EVERY_REQUEST = True  # refresh session expiry on activity
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# --------------------------------------------------------------------
# 📦 Static & Media Files via Google Cloud Storage
# --------------------------------------------------------------------
INSTALLED_APPS += ['storages']

# GCS bucket name (fallback to kasuwa-static)
GS_BUCKET_NAME = config('GS_BUCKET_NAME', default='winimarket-media')
GS_CREDENTIALS = None

# Django Storages settings for static files
class StaticRootGoogleCloudStorage(GoogleCloudStorage):
    location = "static"
    default_acl = None

class MediaRootGoogleCloudStorage(GoogleCloudStorage):
    location = "media"
    default_acl = None

DEFAULT_FILE_STORAGE = "winimarket_app.settings.prod.MediaRootGoogleCloudStorage"
STATICFILES_STORAGE = "winimarket_app.settings.prod.StaticRootGoogleCloudStorage"

# GCS custom domain (optional)
GS_CUSTOM_ENDPOINT = f"https://storage.googleapis.com/{GS_BUCKET_NAME}"

STATIC_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/static/"
MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"

# Optional cache control for better performance
GS_DEFAULT_ACL = None
GS_QUERYSTRING_AUTH = False

# Important: Disable local static/media roots
STATIC_ROOT = None
MEDIA_ROOT = None

# For Django 5+
STORAGES = {
    "default": {
        "BACKEND": "winimarket_app.settings.prod.MediaRootGoogleCloudStorage",
    },
    "staticfiles": {
        "BACKEND": "winimarket_app.settings.prod.StaticRootGoogleCloudStorage",
    },
}