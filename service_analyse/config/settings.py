import os
import sys
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Secrets & mode ───────────────────────────────────────────────
# Railway injecte SECRET_KEY_ANALYSE depuis ses Variables
DEBUG = os.environ.get('DEBUG', 'False') == 'True'  # False par défaut en prod
SECRET_KEY = os.environ.get('SECRET_KEY_ANALYSE')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'dev-secret-service_analyse'
    else:
        raise ImproperlyConfigured('The SECRET_KEY_ANALYSE environment variable must be set in production.')

# ─── Hosts & CSRF ─────────────────────────────────────────────────
ALLOWED_HOSTS = [h for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h]

CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o]

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'corsheaders',
    'stats_app',
    'tests_stat_app',
    'series_app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # NOUVEAU — WhiteNoise juste après SecurityMiddleware pour servir les fichiers statiques
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

# ─── Base de données ───────────────────────────────────────────────
# Railway injecte DATABASE_URL automatiquement quand tu lies un service PostgreSQL.
# dj_database_url parse cette URL et configure Django tout seul.
# Fallback SQLite pour dev local sans DB_HOST.
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif 'test' in sys.argv or not os.environ.get('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME':   BASE_DIR / 'db_local.sqlite3',
        }
    }
else:
    # Dev local avec Docker (variables DB_* classiques)
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     os.environ.get('DB_NAME',     'census_analyse'),
            'USER':     os.environ.get('DB_USER',     'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST':     os.environ.get('DB_HOST',     'localhost'),
            'PORT':     os.environ.get('DB_PORT',     '5432'),
        }
    }

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False') == 'True'

# ─── Fichiers statiques ────────────────────────────────────────────
STATIC_URL  = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'frontend' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# NOUVEAU — WhiteNoise compresse et met en cache les fichiers statiques
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Dakar'
USE_TZ        = True

# ─── URLs inter-services ───────────────────────────────────────────
# Sur Railway, utilise les URLs publiques des autres services
# (ou les domaines privés Railway si tu actives le réseau privé)
SERVICE_IMPORT_URL  = os.environ.get('SERVICE_IMPORT_URL')
SERVICE_ANALYSE_URL = os.environ.get('SERVICE_ANALYSE_URL')
SERVICE_VISU_URL    = os.environ.get('SERVICE_VISU_URL')

if not SERVICE_IMPORT_URL:
    SERVICE_IMPORT_URL = 'http://localhost:8001' if DEBUG else 'https://services-import-production.up.railway.app'
if not SERVICE_ANALYSE_URL:
    SERVICE_ANALYSE_URL = 'http://localhost:8002' if DEBUG else 'https://plateforme-analysis-production.up.railway.app'
if not SERVICE_VISU_URL:
    SERVICE_VISU_URL = 'http://localhost:8003' if DEBUG else 'https://plateforme-visu-production.up.railway.app'