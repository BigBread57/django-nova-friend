from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from nova_friend.models import FriendRequest
from nova_friend.services.check_friend_request import (
    check_if_exists_friend_request,
    check_if_reverse_exists_friend_request,
)
from nova_friend.services.receiver import Receiver

User = get_user_model()


def create_friend_request(
    validated_data: Dict[str, Any],
    sending_user: User,
    locale: str,
) -> FriendRequest:
    # Получаем receiver по информации, переданной в 'contact'.
    receiver = Receiver(
        contact=validated_data['contact'],
        sending_user=sending_user,
        locale=locale,
    )
    receiving_user = receiver.receiving_user_by_contact()

    if sending_user == receiving_user:
        raise ValidationError(
            _('Вы пытаетесь отправить запрос самому себе.'),
        )
    if receiving_user in sending_user.friends.all():
        raise ValidationError(
            _('Пользователь уже добавлен в Ближний круг.'),
        )

    # Проверяем, что FriendRequest с receiving_user и sending_user нет в БД.
    check_if_exists_friend_request(
        sending_user=sending_user,
        receiving_user=receiving_user,
    )
    check_if_reverse_exists_friend_request(
        sending_user=sending_user,
        receiving_user=receiving_user,
    )

    return FriendRequest.objects.create(
        sending_user=sending_user,
        receiving_user=receiving_user,
        contact=validated_data['contact'],
        message=validated_data.get('message', ''),
    )


