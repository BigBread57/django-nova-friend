from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from nova_friend.models import ReferralCode

User = get_user_model()


def create_referral_code(validated_data: Dict[str, Any]) -> ReferralCode:
    """Создание реферального кода."""
    created = False
    while created is False:
        code = get_random_string(8).upper()
        referral_code, created = ReferralCode.objects.get_or_create(
            code=code,
            defaults=validated_data,
        )
    return referral_code
