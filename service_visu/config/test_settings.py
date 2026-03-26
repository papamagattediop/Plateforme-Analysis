"""
Settings de test — SQLite en mémoire pour service_visu.
Usage : python manage.py test --settings=config.test_settings
"""
from .settings import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   ':memory:',
    }
}
