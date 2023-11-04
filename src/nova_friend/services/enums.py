from django.db import models
from django.utils.translation import gettext_lazy as _


class FriendRequestStatus(models.TextChoices):
    """Статус запроса в друзья."""

    PENDING = 'pending', _('Ожидает')
    REJECTED = 'rejected', _('Отклонён')
    CONFIRMED = 'confirmed', _('Подтвержден')
    CANCELED = 'canceled', _('Отменен')


class FriendRequestMode(models.TextChoices):
    """Тип запроса в друзья."""

    INCOMING = 'incoming', _('Входящий')
    OUTCOMING = 'outcoming', _('Исходящий')
