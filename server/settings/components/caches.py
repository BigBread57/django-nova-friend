CACHES = {
    'default': {
        # in production better use other cache,
        # like https://github.com/jazzband/django-redis
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

# Caching
# https://docs.djangoproject.com/en/2.2/topics/cache/
