from typing import Optional

from rest_framework import serializers

from nova_friend.models import FriendRequest
from nova_friend.services.absolute_url import get_absolute_url_before_avatar
from nova_friend.services.enums import FriendRequestMode


class CreateFriendRequestSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового запроса в друзья."""

    class Meta(object):
        model = FriendRequest
        fields = (
            'id',
            'contact',
            'token',
        )
        extra_kwargs = {
            'token': {'read_only': True},
        }


class FriendRequestSerializer(serializers.ModelSerializer):
    """Сериализатор для запроса в друзья."""

    avatar = serializers.SerializerMethodField()
    request_mode = serializers.SerializerMethodField()
    contact_info = serializers.SerializerMethodField()

    class Meta(object):
        model = FriendRequest
        fields = (
            'id',
            'avatar',
            'request_mode',
            'contact_info',
            'token',
        )

    def get_request_mode(  # noqa: WPS615
        self,
        friend_request: FriendRequest,
    ) -> Optional[FriendRequestMode]:
        """Тип запроса: входящий-исходящий."""
        user = self.context['request'].user
        if friend_request.sending_user == user:
            return FriendRequestMode.OUTCOMING
        elif friend_request.receiving_user == user:
            return FriendRequestMode.INCOMING
        return None

    def get_contact_info(  # noqa: WPS615
        self,
        friend_request: FriendRequest,
    ) -> Optional[str]:
        """Получение информации о пользователе исходя из типа запроса."""
        request_mode = self.get_request_mode(friend_request)
        if request_mode == FriendRequestMode.INCOMING:
            return friend_request.sending_user.full_name
        elif request_mode == FriendRequestMode.OUTCOMING:
            return friend_request.receiving_user.full_name
        return None

    def get_avatar(  # noqa: WPS615
        self,
        friend_request: FriendRequest,
    ) -> Optional[str]:
        """Получение аватарки исходя из типа запроса."""
        request_mode = self.get_request_mode(friend_request)
        if request_mode == FriendRequestMode.OUTCOMING:
            return get_absolute_url_before_avatar(
                friend_request.receiving_user.avatar,
            )
        elif request_mode == FriendRequestMode.INCOMING:
            return get_absolute_url_before_avatar(
                friend_request.sending_user.avatar,
            )
        return None
