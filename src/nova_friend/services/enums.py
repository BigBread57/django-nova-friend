from django.db import models
from django.utils.translation import gettext_lazy as _


class FriendRequestStatus(models.TextChoices):
    """Статус запроса в друзья."""

    PENDING = 'pending', _('Ожидает')
    REJECTED = 'rejected', _('Отклонён')
    ACCEPTED = 'accepted', _('Принят')
