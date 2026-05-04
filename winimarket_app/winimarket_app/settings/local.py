from .base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CELERY_BROKER_URL = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL  # using django-celery-results
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

SECURE_COOKIE = config('SECURE_COOKIE', default=False, cast=bool)


FRONTEND_URL = "http://127.0.0.1:8000/account"