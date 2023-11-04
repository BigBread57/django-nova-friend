"""Настройки для создаваемой app."""
from nova_friend.api.serializers import UpdateReferralCodeeSerializer
from server.settings.components import config

MAX_STRING_LENGTH = 255

BASE_USER_SERIALIZER = config(
    'NOVA_USER_DRIVER',
    default='nova_friend.api.serializers.referral_code.ReferralCodeSerializer',
)
