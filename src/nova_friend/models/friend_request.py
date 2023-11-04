import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from nova_friend.services.base_model import AbstractModel
from nova_friend.services.enums import FriendRequestStatus

User = get_user_model()


class FriendRequest(AbstractModel):
    """Запрос на добавление в друзья."""

    sending_user = models.ForeignKey(
        to=User,
        related_name='friend_sending_requests',
        verbose_name=_('Пользователь, запрашивающий добавление в друзья.'),
        on_delete=models.CASCADE,
        db_index=True,
    )
    receiving_user = models.ForeignKey(
        to=User,
        related_name='friend_receiving_requests',
        verbose_name=_('Пользователь, которого добавляют в друзья.'),
        on_delete=models.CASCADE,
        db_index=True,
    )
    message = models.TextField(
        verbose_name=_("Сообщение запроса"),
        blank=True,
    )
    contact = models.CharField(
        verbose_name=_('Номер телефона, email или реферальная ссылка.'),
        max_length=100,  # noqa: WPS432
    )
    token = models.UUIDField(
        verbose_name=_('Token запроса в друзья.'),
        default=uuid.uuid4,
    )
    status = models.CharField(
        verbose_name=_('Статус запроса.'),
        choices=FriendRequestStatus.choices,
        max_length=10,  # noqa: WPS432
        default=FriendRequestStatus.PENDING.value,
    )

    class Meta(AbstractModel.Meta):
        verbose_name = _('Запрос в друзья.')
        verbose_name_plural = _('Запросы в друзья.')

        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=FriendRequestStatus.values),
                name='friend_request_status_valid',
            ),
        ]

    def __str__(self):
        return f'{self.sending_user} -> {self.receiving_user}'
