from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from nova_friend.models import FriendRequest

User = get_user_model()


def check_if_exists_friend_request(
    sending_user: User,
    receiving_user: User,
) -> None:
    """Проверка того, что запрос в друзья уже существует."""
    try:
        friend_request = FriendRequest.objects.get(
            sending_user=sending_user,
            receiving_user=receiving_user,
        )
    except FriendRequest.DoesNotExist:
        return

    if friend_request.is_approved:
        raise ValidationError(
            _('Пользователь уже добавлен в Ближний круг.'),
        )

    raise ValidationError(
        _('Вы уже отправили запрос пользователю. Дождитесь ответа.'),
    )


def check_if_reverse_exists_friend_request(
    sending_user: User,
    receiving_user: User,
) -> None:
    """Проверка того, что обратный запрос в друзья уже существует."""
    try:
        friend_request = FriendRequest.objects.get(
            sending_user=receiving_user,
            receiving_user=sending_user,
        )
    except FriendRequest.DoesNotExist:
        return

    if friend_request.is_approved:
        raise ValidationError(
            _('Пользователь уже добавлен в Ближний круг.'),
        )

    raise ValidationError(
        _('Вам отправлен запрос в друзья от пользователю. Примите решение.'),
    )
