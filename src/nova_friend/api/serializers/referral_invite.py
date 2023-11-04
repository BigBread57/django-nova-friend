from rest_framework import serializers

from nova_friend.api.serializers import ReferralCodeSerializer
from nova_friend.models import ReferralInvite
from nova_friend.services.base_user_serializer import BaseUserSerializer


class ReferralInviteSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра приглашенных по реферальной системе."""

    referral_user = BaseUserSerializer()
    invited_user = BaseUserSerializer()
    referral_code = ReferralCodeSerializer()

    class Meta(object):
        model = ReferralInvite
        fields = (
            'id',
            'referral_user',
            'invited_user',
            'referral_code',
        )
