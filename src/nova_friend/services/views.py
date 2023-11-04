import uuid

from rest_framework.exceptions import NotFound

from server.apps.nova_account.models import FriendRequest
from server.apps.nova_account.services.enums import FriendRequestStatus
from server.apps.nova_notification.models import Notification
from server.apps.nova_notification.models.notification import TypeNotification


def notification_accepted_false(
    account_id: int,
    related_object_id: int,
) -> None:
    """Изменяем активность уведомления.

    Логика необходима для того, чтобы убрать кнопки у уведомления,
    по которому уже были совершены действия.
    """
    # Ищем активные уведомления о том, что пользователя хотят добавить в
    # друзья.
    notifications = Notification.objects.filter(
        account_id=account_id,
        related_object_id=related_object_id,
        type=TypeNotification.FRIEND,
        is_active=True,
        is_read=False,
    )
    # Если уведомление не найдено, то ничего не делаем, иначе меняем активность.
    # Смена активности нужна, чтобы кнопки по уведомлению были не доступны.
    if notification := notifications.first():
        notification.is_active = False
        notification.is_read = True
        notification.save(update_fields=['is_read', 'is_active'])


def friend_request_by_token(token: uuid.UUID) -> FriendRequest:
    """Получить FriendRequest или raise NotFound."""
    try:
        friend_request = FriendRequest.objects.get(
            token=token,
            is_approved=False,
        )
    except FriendRequest.DoesNotExist as exc:
        raise NotFound from exc
    return friend_request


def confirm_friend_request(token: uuid.UUID) -> FriendRequest:
    """Логика подтверждения запроса в друзья."""
    # Получаем FriendRequest по токену, если он существует.
    friend_request = friend_request_by_token(token)

    # Меняем статус приглашения в друзья.
    friend_request.is_approved = True
    friend_request.status = FriendRequestStatus.ACCEPTED
    friend_request.save(update_fields=['is_approved', 'status'])

    # Добавляем пользователя в друзья.
    account = friend_request.receiving_account
    account.friends.add(friend_request.sending_account)
    account.save()

    # Меняем активность уведомления, по которому пользователя (получателя)
    # хотят добавить в друзья.
    notification_accepted_false(
        account_id=friend_request.receiving_account.id,
        related_object_id=friend_request.id,
    )

    return friend_request


def reject_friend_request(token: uuid.UUID) -> None:
    """Логика отказа от дружбы со стороны получателя запроса."""
    # Получаем FriendRequest по токену, если он существует.
    friend_request = friend_request_by_token(token)

    # Костыль, для того, чтобы пользователь получил уведомление о том,
    # что его запрос в друзья отклонен.
    friend_request.status = FriendRequestStatus.REJECTED
    friend_request.save(update_fields=['status'])

    # Меняем активность уведомления, по которому пользователя (получателя)
    # хотят добавить в друзья.
    notification_accepted_false(
        account_id=friend_request.receiving_account.id,
        related_object_id=friend_request.id,
    )

    # Удаляем запрос в друзья.
    friend_request.delete()


def cancel_friend_request(token: uuid.UUID) -> None:
    """Логика отказа от дружбы со стороны отправителя запроса."""
    # Получаем FriendRequest по токену, если он существует.
    friend_request = friend_request_by_token(token)

    # Меняем активность уведомления, по которому пользователя (получателя)
    # хотят добавить в друзья.
    notification_accepted_false(
        account_id=friend_request.receiving_account.id,
        related_object_id=friend_request.id,
    )

    # Удаляем запрос в друзья.
    friend_request.delete()
