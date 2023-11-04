from typing import Optional

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from nova_friend.models import FriendRequest
from nova_friend.services.receiver import Receiver


class NewFriendRequestSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового запроса в друзья."""

    class Meta(object):
        model = FriendRequest
        fields = (
            'contact',
            'token',
        )
        extra_kwargs = {
            'token': {'read_only': True},
        }

    def create(self, validated_data):
        """Создание нового FriendRequest."""
        # Получаем данные отправителя - пользователя, который хочет добавить
        # кого-то в друзья.
        request = self.context['request']
        sender = request.user

        # Получаем receiver по информации, переданной в 'contact'
        receiver = Receiver(
            contact=validated_data['contact'],
            user=sender,
            locale=request.LANGUAGE_CODE,
        )
        receiver = receiver.receiver_by_contact()

        if sender == receiver:
            raise ValidationError(
                _('Вы пытаетесь отправить запрос самому себе.'),
            )
        if receiver in sender.friends.all():
            raise ValidationError(
                _('Пользователь уже добавлен в Ближний круг.'),
            )

        # Проверяем что пользователя могут приглашать в друзья и в его
        # настройках приватности не стоит ограничений.
        check_invitation_from_other_users(account_id=receiver.id)

        validated_data['sending_account'] = sender
        validated_data['receiving_account'] = receiver

        # Проверяем, что FriendRequest с receiver и sender нет в БД.
        check_if_exists_fr(validated_data)
        check_if_reverse_exists_fr(validated_data)

        return super().create(validated_data)


class FriendRequestSerializer(serializers.ModelSerializer):
    """Сериализатор для запроса в друзья."""

    avatar = serializers.SerializerMethodField(read_only=True)
    request_mode = serializers.SerializerMethodField(read_only=True)
    contact_info = serializers.SerializerMethodField(read_only=True)

    class Meta(object):
        model = FriendRequest
        fields = [
            'avatar',
            'request_mode',
            'contact_info',
            'token',
        ]

    def get_request_mode(  # noqa: WPS615
        self,
        friend_request: FriendRequest,
    ) -> Optional[FriendRequestMode]:
        """Тип запроса: входящий-исходящий."""
        user = self.context['request'].user
        if friend_request.sending_account.user == user:
            return FriendRequestMode.OUTCOMING
        elif friend_request.receiving_account.user == user:
            return FriendRequestMode.INCOMING
        return None

    def get_contact_info(  # noqa: WPS615
        self,
        friend_request: FriendRequest,
    ) -> Optional[str]:
        """Получение поля contact_info."""
        mode = self.get_request_mode(friend_request)
        if mode == FriendRequestMode.INCOMING:
            return str(friend_request.sending_account.user.full_name)
        elif mode == FriendRequestMode.OUTCOMING:
            return str(friend_request.receiving_account.user.full_name)
        return None

    def get_avatar(  # noqa: WPS615
        self,
        friend_request: FriendRequest,
    ) -> Optional[str]:
        """Получение аватарки исходя из типа запроса."""
        if self.get_request_mode(friend_request) == FriendRequestMode.OUTCOMING:
            return get_absolute_url_before_avatar(
                friend_request.receiving_account.avatar,
            )
        elif self.get_request_mode(friend_request) == FriendRequestMode.INCOMING:  # noqa: E501
            return get_absolute_url_before_avatar(
                friend_request.sending_account.avatar,
            )
        return None
