import os
import sys
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY_VISU', 'dev-secret-service_visu')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')


def normalize_service_url(value, default):
    if not value:
        return default
    value = value.strip()
    if value.startswith('http://') or value.startswith('https://'):
        return value
    return f'https://{value}'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'corsheaders',
    'cartes_app',
    'dashboard_app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.service_urls',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# SQLite en local (tests / dev sans Docker), PostgreSQL sinon
DATABASE_URL = os.environ.get('DATABASE_URL')
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME':   BASE_DIR / 'db_local.sqlite3',
        }
    }
elif DATABASE_URL:
    db = urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db.path[1:],
            'USER': db.username,
            'PASSWORD': db.password,
            'HOST': db.hostname,
            'PORT': db.port or 5432,
        }
    }
elif os.environ.get('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     os.environ.get('DB_NAME',     'census_visu'),
            'USER':     os.environ.get('DB_USER',     'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST':     os.environ.get('DB_HOST',     'localhost'),
            'PORT':     os.environ.get('DB_PORT',     '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME':   BASE_DIR / 'db_local.sqlite3',
        }
    }

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

CORS_ALLOW_ALL_ORIGINS = True

STATIC_URL  = '/static/'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'frontend' / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Dakar'
USE_TZ        = True

# URLs inter-services
SERVICE_IMPORT_URL = normalize_service_url(
    os.environ.get('SERVICE_IMPORT_URL'),
    'http://localhost:8001' if DEBUG else 'https://services-import-production.up.railway.app'
)
SERVICE_ANALYSE_URL = normalize_service_url(
    os.environ.get('SERVICE_ANALYSE_URL'),
    'http://localhost:8002' if DEBUG else 'https://plateforme-analysis-production.up.railway.app'
)
SERVICE_VISU_URL = normalize_service_url(
    os.environ.get('SERVICE_VISU_URL'),
    'http://localhost:8003' if DEBUG else 'https://plateforme-visu-production.up.railway.app'
)
