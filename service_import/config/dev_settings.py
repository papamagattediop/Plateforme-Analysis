"""
Settings pour lancement local (sans Docker/PostgreSQL/Redis).
Usage : DJANGO_SETTINGS_MODULE=config.dev_settings python manage.py runserver
"""
from .settings import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   BASE_DIR / 'db_local.sqlite3',
    }
}

# Celery synchrone (pas besoin de Redis)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
