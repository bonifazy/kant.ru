from pathlib import Path
import logger.apps

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PARENT = Path(__file__).resolve().parent.parent.parent.joinpath('data/')  # folder to database
DB_FILE = DB_PARENT.joinpath('db.sqlite3')
PROJECT_ROOT = BASE_DIR

with open('.django_secret') as f:
    SECRET_KEY = f.read().strip()

DEBUG = True  # True- dev, False- prod

if DEBUG:  # dev
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
else:  # prod
    ALLOWED_HOSTS = ['marchdim.dev', 'www.marchdim.dev', '134.209.88.84', 'localhost']
    

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'logger.apps.LoggerConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kant.urls'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR.joinpath('static/')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR.joinpath('templates/')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kant.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_FILE,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if DEBUG:  # dev
    SECURE_HSTS_SECONDS = 600
    SECURE_SSL_REDIRECT = False
else:  # prod
    SECURE_HSTS_SECONDS = 31536000
    SECURE_SSL_REDIRECT = True

#SECURE_CONTENT_TYPE_NOSNIFF = True
#SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#SESSION_COOKIE_SECURE = True
#SECURE_HSTS_PRELOAD = True
#CSRF_COOKIE_SECURE = True

