"""
Django's settings for Tara project.

Generated by 'django-admin startproject' using Django 4.2.16.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
import base64
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-+9)9852a8&af5dmne4@fgjxcn8q7)65losj40_3&hy^d1+x2ku'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'localhost',  # Local development
    '127.0.0.1',  # Local development
    '35.154.44.198',  # Replace with your actual domain
    'ec2-35-154-44-198.ap-south-1.compute.amazonaws.com',  # EC2 public DNS
    'api.ipify.org',  # Add this if your app needs to handle requests from this domain
    '*',
    'dev.tarafirst.com'
]

CORS_ORIGIN_ALLOW_ALL =True

# Define base directory and log path
LOG_PATH = os.path.join(BASE_DIR, 'log')

# Application definition

INSTALLED_APPS = [
    # 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user_management',
    'drf_yasg',
    'rest_framework_simplejwt',
    'corsheaders',
    'invoicing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'Tara.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Ensure this directory exists and is listed
        ],
        'APP_DIRS': True,  # This allows Django to look for templates in each app's "templates" directory
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


WSGI_APPLICATION = 'Tara.wsgi.application'
ASGI_APPLICATION = 'Tara.asgi.application'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# In Tara/settings/default.py
AUTH_USER_MODEL = 'user_management.User'


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'

# Directory where static files will be collected
STATIC_ROOT = os.path.join(BASE_DIR, '../staticfiles')

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'static'),  # Root-level static files
#     os.path.join(BASE_DIR, 'Tara', 'static'),  # Static files inside the 'Tara' app
# ]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Tara/settings/default.py

# Disable migrations for certain built-in apps
MIGRATION_MODULES = {
    'auth': None,
    'admin': None,
}


FRONTEND_URL = 'http://dev.tarafirst.com/'


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


# Set the log level based on the environment
ENVIRONMENT = os.getenv('DJANGO_ENV', 'local')  # Default to 'local' if DJANGO_ENV is not set
LOG_LEVEL = 'DEBUG' if ENVIRONMENT in ['local', 'development'] else 'ERROR'


# Define log directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure the 'logs' directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    # Version of logging
    'version': 1,
    # disable logging
    'disable_existing_loggers': False,
    # Formatter
    'formatters': {
        'log_format': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[%(server_time)s] %(message)s',
        }
    },
    # Handlers #############################################################
    'handlers': {
        'file': {
            # 'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'log_format',
            'filename': 'application.log',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'log_format'
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        }
    },
    # Loggers ####################################################################
    'loggers': {
        '': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': True,
        },
        'gunicorn': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
            # 'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG')
        },
    },
}


################ master gst

MASTER_GST_EMAIL = os.getenv('MASTER_GST_EMAIL')
MASTER_GST_CLIENT_ID = os.getenv('MASTER_GST_CLIENT_ID')
MASTER_GST_SECRET_KEY = os.getenv('MASTER_GST_SECRET_KEY')

############# Zerobounce email validation
ZEROBOUNCE_EMAIL = os.getenv('ZEROBOUNCE_EMAIL')
ZEROBOUNCE_SECRET_KEY = os.getenv('ZEROBOUNCE_SECRET_KEY')

################


RAZORPAY_CLIENT_ID = os.getenv('RAZORPAY_CLIENT_ID')

RAZORPAY_CLIENT_SECRET = os.getenv('RAZORPAY_CLIENT_SECRET')

SANDBOX_API_KEY = os.getenv('SANDBOX_API_KEY')
SANDBOX_API_SECRET = os.getenv('SANDBOX_API_SECRET')
SANDBOX_API_URL = os.getenv('SANDBOX_API_URL')
SANDBOX_API_VERSION = os.getenv('SANDBOX_API_VERSION')


# Load the secret encryption key
SECRET_ENCRYPTION_KEY = os.getenv("SECRET_ENCRYPTION_KEY", "default-fallback-key")

AWS_REGION = os.getenv('AWS_REGION')  # e.g., "us-east-1"
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')


DATABASES = {
        'default': {
            'ENGINE': 'djongo',
            'NAME': 'development',
            'ENFORCE_SCHEMA': False,
            'CLIENT': {
                'host': 'mongodb+srv://Development:jJ649y2MEH99Ykdu@cluster0.xozfe.mongodb.net/development'
                        '?tls=true&tlsAllowInvalidCertificates=true',
                'port': 27017,
                'username': 'Development',
                'password': 'jJ649y2MEH99Ykdu',
                'authSource': 'admin',
                'authMechanism': 'SCRAM-SHA-1',
                'tls': True,
                'tlsAllowInvalidCertificates': True
            },
            'CONN_MAX_AGE': None
        }
}


Reference_link = "http://dev.tarafirst.com/"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR)+'/templates'],
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
