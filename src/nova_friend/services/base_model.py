from django.db import models
from django.utils.translation import gettext_lazy as _
from rules.contrib.models import RulesModel


class AbstractModel(RulesModel):
    """Базовая модель."""

    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Изменен"), auto_now=True)

    class Meta(object):
        abstract = True
        ordering = ['-id']
