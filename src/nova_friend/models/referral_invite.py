
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from nova_friend.services.base_model import AbstractModel

User = get_user_model()


class ReferralInvite(AbstractModel):
    """Приглашенные по реферальной системе."""

    referral_user = models.ForeignKey(
        to=User,
        related_name='referral_users',
        verbose_name=_('Пользователь, который пригласил.'),
        on_delete=models.CASCADE,
        db_index=True,
    )
    invited_user = models.ForeignKey(
        to=User,
        related_name='invited_users',
        verbose_name=_('Пользователь, которого пригласили.'),
        on_delete=models.CASCADE,
        db_index=True,
    )

    class Meta(AbstractModel.Meta):
        verbose_name = _('Приглашенный по реферальной системе.')
        verbose_name_plural = _('Приглашенные по реферальной системе.')

    def __str__(self):
        return f'{self.referral_user} -> {self.invited_user}'
