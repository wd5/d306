# -*- coding: utf-8 -*-
# Django settings for uralsocionics project.
import os

DEBUG = False
TEMPLATE_DEBUG = False
APPEND_SLASH = False

ADMINS = (
    ('Glader', 'glader.ru@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'NAME': 'd306',
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'd306',
        'PASSWORD': ''
    }
}

LOGIN_REDIRECT_URL = '/'

AUTH_PROFILE_MODULE = 'madera_site.Profile'

PROJECT_PATH = os.path.dirname(__file__)
data_images_path = './media/data/'
FORCE_SCRIPT_NAME = ""

TIME_ZONE = 'Asia/Yekaterinburg'
LANGUAGE_CODE = 'ru-ru'
SITE_ID = 1
USE_I18N = True

MEDIA_ROOT = STATIC_ROOT = PROJECT_PATH + '/media/'
MEDIA_URL = STATIC_URL = '/media/'
SECRET_KEY = '12345'
DOMAIN = 'd306.ru'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.csrf',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'madera_site.middleware.CheckProfile',
)

ROOT_URLCONF = 'urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'pytils',
    'tagging',
    'south',
    'madera_site',
    'django_subscribe',
)

SERVER_EMAIL = DEFAULT_FROM_EMAIL = 'glader.ru@gmail.com'

LOG_PATH = '/var/log/projects/d306'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(name)-15s %(levelname)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_PATH, 'traceback.log'),
            'formatter': 'verbose',
        },
        'email_log': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_PATH, 'email.log'),
            'formatter': 'verbose',
            },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.email': {
            'handlers': ['email_log'],
            'level': 'INFO',
            'propagate': False,
            },
    }
}

try:
    from local_settings import *
except ImportError:
    pass
