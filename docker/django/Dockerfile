# syntax=docker/dockerfile:1

# This Dockerfile uses multi-stage build to customize DEV and PROD images:
# https://docs.docker.com/develop/develop-images/multistage-build/

FROM hub.letsnova.com/p/python:3.11-slim-bookworm AS base_build

LABEL maintainer="nova@letsnova.ru"
LABEL vendor="nova"

ENV \
  # build:
  BUILD_ONLY_PACKAGES='wget' \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_CACHE_DIR=/var/cache/pip \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_INDEX_URL=https://pypi.letsnova.ru/simple/ \
  # dockerize:
  USE_DOCKER=1 \
  # poetry:
  POETRY_VERSION=1.7.0 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  PYTHONPATH=/code/src


# System deps:
RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    gettext \
    # Defining build-time-only dependencies:
    $BUILD_ONLY_PACKAGES \
  # Removing build-time-only dependencies:
  && apt-get remove -y $BUILD_ONLY_PACKAGES \
  # Cleaning cache:
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# This is a special case. We need to run this script as an entry point:
COPY ./docker/django/entrypoint.sh /docker-entrypoint.sh

# Setting up proper permissions:
RUN chmod +x '/docker-entrypoint.sh' \
  && groupadd -r web && useradd -d /code -r -g web web \
  && chown web:web -R /code \
  && mkdir -p /var/www/django/static /var/www/django/media \
  && chown web:web /var/www/django/static /var/www/django/media

# Copy only requirements, to cache them in docker layer
COPY --chown=web:web ./poetry.lock ./pyproject.toml /code/

FROM base_build as ci

# Project initialization:
RUN \
  --mount=type=cache,id=pip,target="$PIP_CACHE_DIR",sharing=shared,mode=0755 \
  --mount=type=cache,id=poetry,target="$POETRY_CACHE_DIR",sharing=shared,mode=0755 \
    poetry install --no-root \
  # Устанавливаем poetry заново, так как блядский poetry при установке удаляет
  # свои же зависимости
  && pip install "poetry==$POETRY_VERSION"


ARG DJANGO_ENV
ENV DJANGO_ENV=${DJANGO_ENV}

# Running as non-root user:
USER web

# We customize how our app is loaded with the custom entrypoint:
ENTRYPOINT ["tini", "--", "/docker-entrypoint.sh"]
