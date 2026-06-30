"""
Configuración de Django para StreamMusic.

IMPORTANTE: este proyecto NO usa el ORM de Django ni una base de datos SQL.
Todo el acceso a datos se hace con PyMongo contra MongoDB Atlas (ver core/db.py).
Por eso DATABASES queda vacío y no se incluyen apps que dependan del ORM
(django.contrib.auth, admin, contenttypes).
"""
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga las variables del archivo .env (MONGO_URI, MONGO_DB, etc.) al entorno.
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'clave-de-desarrollo-no-usar-en-produccion')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    # Solo las apps que NO requieren una base de datos SQL/ORM.
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'django.contrib.messages',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Las sesiones se guardan en una cookie firmada (no en base de datos), ya que
# este proyecto no tiene ninguna base de datos SQL configurada.
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

ROOT_URLCONF = 'streammusic.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'streammusic.wsgi.application'

# Sin base de datos SQL: todo el acceso a datos es vía PyMongo (core/db.py).
DATABASES = {}

LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Para que messages.error() se muestre con la clase "alert-danger" de
# Bootstrap (por defecto Django usaría la clase "alert-error", que no existe).
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.ERROR: 'danger',
}

# --- Configuración propia de MongoDB (leída por core/db.py) ---
MONGO_URI = os.environ.get('MONGO_URI')
MONGO_DB = os.environ.get('MONGO_DB', 'StreamMusic')
