from typing import Optional

from django.conf import settings


def get_absolute_url_before_avatar(avatar) -> Optional[str]:
    """Абсолютный путь до фотографии пользователя."""
    if avatar:
        return f'https://{settings.DOMAIN_NAME}{avatar.url}'  # type: ignore
    return None
