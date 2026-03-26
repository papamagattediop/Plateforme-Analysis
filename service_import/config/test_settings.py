"""
Settings de test — remplace PostgreSQL par SQLite en mémoire.
Usage : python manage.py test --settings=config.test_settings
"""
from .settings import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   ':memory:',
    }
}

# Désactiver Celery pendant les tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
