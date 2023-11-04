import uuid

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import NotFound

from nova_friend import signals
from nova_friend.models import FriendRequest
from nova_friend.services.enums import FriendRequestStatus


def friend_request_by_token(token: uuid.UUID) -> FriendRequest:
    """Получить FriendRequest или raise NotFound."""
    try:
        return FriendRequest.objects.get(
            token=token,
            status=FriendRequestStatus.PENDING,
        )
    except FriendRequest.DoesNotExist:
        raise NotFound(_('Запрос на добавление в друзья не найден.'))


def friend_request_action(
    token: uuid.UUID,
    status: str,
) -> None:
    """Логика подтверждения запроса в друзья."""
    # Получаем FriendRequest по токену, если он существует.
    friend_request = friend_request_by_token(token)

    # Меняем статус приглашения в друзья.
    friend_request.status = status
    friend_request.save(update_fields=['status'])

    signals.friend_request_action.send(
        sender='friend_request_action',
        status=status,
        friend_request_id=friend_request.id,
        sending_user_id=friend_request.sending_user.id,
        receiving_user_id=friend_request.receiving_user.id,
    )

    if status in {FriendRequestStatus.CANCELED, FriendRequestStatus.REJECTED}:
        # Удаляем запрос в друзья.
        friend_request.delete()
