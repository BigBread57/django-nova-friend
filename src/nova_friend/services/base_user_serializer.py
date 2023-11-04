from django.conf import settings
from django.utils.module_loading import import_string

"""Получить сериализатор для отображения информации о пользователе."""
class_path = getattr(
    settings,
    'BASE_USER_SERIALIZER',
    'nova_friend.api.serializers.referral_code.ReferralCodeSerializer',
)
BaseUserSerializer = import_string(class_path)
