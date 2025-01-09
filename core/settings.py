import os
import environ
from datetime import timedelta

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env()


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
VALID_API_KEYS = env.str("VALID_API_KEYS").split(",")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CORS_ORIGIN_WHITELIST = env.list("CORS_ORIGIN_WHITELIST")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

SITE_ID = 1

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    "django.contrib.sites",
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

PROJECT_APPS = [
    'apps.authentication',
    'apps.user_profile',
    'apps.media',
    'apps.blog',
    'apps.newsletter',
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
    'rest_framework_api',
    'channels',
    'ckeditor',
    'ckeditor_uploader',
    'django_celery_results',
    'django_celery_beat',
    'djoser',
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    'axes',
    'storages'
]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + THIRD_PARTY_APPS

CKEDITOR_CONFIGS = {"default": {"toolbar": "full", "autoParagraph": False}}
CKEDITOR_UPLOAD_PATH = "media/"

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = lambda request: timedelta(minutes=5)
AXES_LOCK_OUT_AT_FAILURE = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    # It only formats user lockout messages and renders Axes lockout responses
    # on failed user authentication attempts from login views.
    # If you do not want Axes to override the authentication response
    # you can skip installing the middleware and use your own views.
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("DATABASE_NAME"),
        'USER': env("DATABASE_USER"),
        'PASSWORD': env("DATABASE_PASSWORD"),
        'HOST': env("DATABASE_HOST"),
        'PORT': 5432
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

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


# # Static files (CSS, JavaScript, Images)
# # https://docs.djangoproject.com/en/4.2/howto/static-files/

# STATIC_LOCATION = "static"
# STATIC_URL = 'static/'
# STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly"
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication"
    ]
}

AUTHENTICATION_BACKENDS = (
    # AxesStandaloneBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    'axes.backends.AxesStandaloneBackend',

    "django.contrib.auth.backends.ModelBackend",
)

AUTH_USER_MODEL = "authentication.UserAccount"

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("JWT",),
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=60),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "SIGNING_KEY": env("SECRET_KEY"),
}

DJOSER = {
    'LOGIN_FIELD': "email",
    'USER_CREATE_PASSWORD_RETYPE': True,
    "USERNAME_CHANGED_EMAIL_CONFIRMATION": True,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
    "SEND_CONFIRMATION_EMAIL": True,
    "SEND_ACTIVATION_EMAIL": True,

    'PASSWORD_RESET_CONFIRM_URL': 'forgot-password-confirm/?uid={uid}&token={token}',
    'USERNAME_RESET_CONFIRM_URL': 'email/username_reset_confirm/{uid}/{token}',
    'ACTIVATION_URL': 'activate/?uid={uid}&token={token}',

    'SERIALIZERS': {
        "user_create": "apps.authentication.serializers.UserCreateSerializer",
        "user": "apps.authentication.serializers.UserSerializer",
        "current_user": "apps.authentication.serializers.UserSerializer",
        "user_delete": "djoser.serializers.UserDeleteSerializer"
    },

    'TEMPLATES': {
        "activation": "email/auth/activation.html",
        "confirmation": "email/auth/confirmation.html",
        "password_reset": "email/auth/password_reset.html",
        "password_changed_confirmation": "email/auth/password_changed_confirmation.html",
        "username_changed_confirmation": "email/auth/username_changed_confirmation.html",
        "username_reset": "email/auth/username_reset.html",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL")]
        }
    }
}

REDIS_HOST = env("REDIS_HOST")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

CHANNELS_ALLOWED_ORIGINS = "http://localhost:3000"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Lima"

CELERY_BROKER_URL = env("REDIS_URL")
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
    'socket_timeout': 5,
    'retry_on_timeout': True
}

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'

CELERY_IMPORTS = (
    'core.tasks',
    'apps.blog.tasks'
)

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Configuracion de Cloudfront
AWS_CLOUDFRONT_DOMAIN=env("AWS_CLOUDFRONT_DOMAIN")
AWS_CLOUDFRONT_KEY_ID =env.str("AWS_CLOUDFRONT_KEY_ID").strip()
AWS_CLOUDFRONT_KEY =env.str("AWS_CLOUDFRONT_KEY", multiline=True).encode("ascii").strip()

# Configuraciones de AWS
AWS_ACCESS_KEY_ID=env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME=env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME=env("AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN=f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"

# Configuración de seguridad y permisos
AWS_QUERYSTRING_AUTH = False # Deshabilita las firmas en las URLs (archivos públicos)
AWS_FILE_OVERWRITE = False # Evita sobrescribir archivos con el mismo nombre
AWS_DEFAULT_ACL = None # Define el control de acceso predeterminado como público
AWS_QUERYSTRING_EXPIRE = 5 # Tiempo de expiración de las URLs firmadas

# Parámetros adicionales para los objetos de S3
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400" # Habilita el almacenamiento en caché por un día
}

# Configuración de archivos estáticos
STATIC_LOCATION = "static"
STATIC_URL = f"{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/"
STATICFILES_STORAGE = "core.storage_backends.StaticStorage"

# Configuración de archivos de medios
MEDIA_LOCATION = "media"
MEDIA_URL = f"https://{AWS_CLOUDFRONT_DOMAIN}/{MEDIA_LOCATION}/"
DEFAULT_FILE_STORAGE = "core.storage_backends.PublicMediaStorage"


if not DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_PORT = env("EMAIL_PORT")
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = env("EMAIL_USE_TLS") == "True"
    DEFAULT_FROM_EMAIL = "Uridium <no-reply@uridium.finance>"