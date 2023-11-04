from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NovaFriendConfig(AppConfig):
    """Конфиг приложения "Друзья"."""

    name = 'nova_friend'
    verbose_name = _('Друзья.')

    def ready(self) -> None:
        """Подключение прав происходит при подключении app."""
        super().ready()
        import nova_friend.api.routers
        import nova_friend.permissions
