from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from nova_friend.services.base_model import AbstractModel

User = get_user_model()


class ReferralCode(AbstractModel):
    """Реферальный код."""

    user = models.ForeignKey(
        to=User,
        related_name='referral_codes',
        verbose_name=_('Пользователь, владелец реферального кода.'),
        on_delete=models.CASCADE,
        db_index=True,
    )
    code = models.CharField(
        verbose_name=_('Реферальный код.'),
        max_length=8,  # noqa: WPS432
        unique=True,
    )
    note = models.CharField(
        verbose_name=_('Примечание'),
        max_length=settings.MAX_STRING_LENGTH,  # type: ignore
    )

    class Meta(AbstractModel.Meta):
        verbose_name = _('Реферальный код.')
        verbose_name_plural = _('Реферальные коды.')

    def __str__(self):
        return f'{self.user} -> {self.code}'
