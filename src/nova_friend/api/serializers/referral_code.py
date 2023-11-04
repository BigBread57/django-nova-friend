from rest_framework import serializers

from nova_friend.models import ReferralCode
from nova_friend.services.base_user_serializer import BaseUserSerializer


class ReferralCodeSerializer(serializers.ModelSerializer):
    """Сериализатор реферального кода."""

    user = BaseUserSerializer()

    class Meta(object):
        model = ReferralCode
        fields = (
            'id',
            'user',
            'code',
            'note',
        )


class CreateReferralCodeSerializer(serializers.ModelSerializer):
    """Сериализатор создания реферального кода."""

    class Meta(object):
        model = ReferralCode
        fields = (
            'id',
            'user',
            'note',
        )


class UpdateReferralCodeSerializer(serializers.ModelSerializer):
    """Сериализатор изменения реферального кода."""

    class Meta(object):
        model = ReferralCode
        fields = (
            'id',
            'note',
        )
