"""
This file contains all the settings used in production.

This file is required and if development.py is present these
values are overridden.
"""

from server.settings.components import config

# Production flags:
# https://docs.djangoproject.com/en/2.2/howto/deployment/

DEBUG = config('DJANGO_DEBUG', cast=bool, default=False)

DOMAIN_NAMES = config(
    'DOMAIN_NAME',
    default=config('ALLOWED_HOSTS', default=''),
).replace(' ', '').split(',')

ALLOWED_HOSTS = [
    # TODO: check production hosts
    *DOMAIN_NAMES,
    # We need this value for `healthcheck` to work:
    'localhost',
]

# CORS settings
CORS_ALLOW_CREDENTIALS = config(
    'CORS_ALLOW_CREDENTIALS',
    cast=bool,
    default=False,
)
CSRF_COOKIE_HTTPONLY = config(
    'CSRF_COOKIE_HTTPONLY',
    cast=bool,
    default=True,
)
SESSION_COOKIE_HTTPONLY = config(
    'SESSION_COOKIE_HTTPONLY',
    cast=bool,
    default=True,
)

# Staticfiles
# https://docs.djangoproject.com/en/2.2/ref/contrib/staticfiles/

# This is a hack to allow a special flag to be used with `--dry-run`
# to test things locally.
_COLLECTSTATIC_DRYRUN = config(
    'DJANGO_COLLECTSTATIC_DRYRUN', cast=bool, default=False,
)
# Adding STATIC_ROOT to collect static files via 'collectstatic':
STATIC_ROOT = (
    '.static' if _COLLECTSTATIC_DRYRUN else '/var/www/django/static'
)

STATICFILES_STORAGE = (
    # This is a string, not a tuple,
    # but it does not fit into 80 characters rule.
    'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
)

# Media files
# https://docs.djangoproject.com/en/2.2/topics/files/

MEDIA_ROOT = '/var/www/django/media'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

# линтер ошибочно полагает, что это пароль
_PASS = 'django.contrib.auth.password_validation'  # noqa: S105
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': '{0}.UserAttributeSimilarityValidator'.format(_PASS)},
    {'NAME': '{0}.MinimumLengthValidator'.format(_PASS)},
    {'NAME': '{0}.CommonPasswordValidator'.format(_PASS)},
    {'NAME': '{0}.NumericPasswordValidator'.format(_PASS)},
]

# Security
# https://docs.djangoproject.com/en/2.2/topics/security/

SECURE_HSTS_SECONDS = 31536000  # the same as Caddy has
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', cast=bool, default=True)
SECURE_REDIRECT_EXEMPT = [
    # This is required for healthcheck to work:
    '^health/',
]

SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', cast=bool, default=True)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', cast=bool, default=True)

CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', cast=str, default='Lax')
SESSION_COOKIE_SAMESITE = config(
    'SESSION_COOKIE_SAMESITE',
    cast=str,
    default='Lax',
)

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        # If you use MultiPartFormParser or FormParser,
        # we also have a camel case version
        'djangorestframework_camel_case.parser.CamelCaseFormParser',
        'djangorestframework_camel_case.parser.CamelCaseMultiPartParser',
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
    ),
    'JSON_UNDERSCOREIZE': {
        'no_underscore_before_number': True,
    },
}
