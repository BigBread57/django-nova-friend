import re
from datetime import datetime
from os import environ
from typing import Dict

import phonenumbers
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template.loader import get_template
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from phonenumber_field.validators import validate_international_phonenumber
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)

from nova_friend import signals

User = get_user_model()


def get_link_with_referral(user_email: str) -> str:
    """Ссылка с referral для понимания того, кто пригласил пользователя."""
    domain_name = settings.DOMAIN_NAME  # type: ignore
    return f'https://{domain_name}/referral?user_email={user_email}'


def check_invitation_from_other_users(account_id: int) -> None:
    """Получение настроек пользователя.

    Проверяем атрибут, который отвечает за "Можно ли другим пользователям
    приглашать вас в ближний круг".
    """
    customization = Customization.objects.get(account_id=account_id)
    if customization.invitation_from_other_users:
        return
    raise PermissionDenied(
        _('Нельзя пригласить пользователя из-за его настроек приватности.'),
    )


class LinkFormation(APIException):
    """Вызов исключения во время создания FriendRequest по link."""

    status_code = status.HTTP_204_NO_CONTENT
    default_detail = _('Формирование ссылки.')
    default_code = 'link_formation'


class LimitExceeded(APIException):
    """Вызов исключения во время создания FriendRequest по link."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Превышен лимит приглашений друзей в ближний круг.')
    default_code = 'limit_exceeded'


class Receiver(object):
    """Класс для получения корректного receiver для запроса в друзья."""

    def __init__(  # noqa: WPS211
        self,
        contact: str,
        user: User,
        locale: str,
    ):
        """Установка переменных."""
        self.contact = contact
        self.user = user
        self.locale = locale

    def receiver_by_contact(self) -> User:  # noqa: C901
        """Получатель запроса на дружбу по строке contact."""
        # Получаем ключевое слово link для формирования ссылки.
        # В таком случае мы не создаем FriendRequest, а вызываем исключение
        # с необходимой информацией.
        if self.contact == 'link':
            raise LinkFormation(
                {
                    'link': get_link_with_referral(self.user.email),
                    'text': _(
                        'Ваша персональная ссылка для приглашения в систему ' +
                        'или добавления пользователя в друзья. Поделитесь ей ' +
                        'удобным для вас способом!',
                    ),
                },
            )

        # Поиск пользователя по e-mail. Начальное условие нужно для запуска
        # валидации
        elif '@' in self.contact:  # noqa: E501
            try:
                validate_email(self.contact)
            except DjangoValidationError:
                raise ValidationError(
                    _('Введен некорректный адрес электронной почты.'),
                )
            return self.user_by_email()

        # Поиск пользователя по телефону. Перед валидацией, удаляем все,
        # кроме цифр и знака +
        mb_numbers = ''.join(re.findall(r'^\+|\d', self.contact))
        try:
            validate_international_phonenumber(mb_numbers)
        except DjangoValidationError:
            raise ValidationError(
                _('Введен некорректный номер телефона.'),
            )
        return self.user_by_phone(mb_numbers)

    def user_by_email(self) -> User:  # type: ignore
        """Account по почте.

        Contact содержит электронную почту пользователя, которого хотели
        добавить в друзья.
        """
        # Ищем пользователя в БД. Если не находим отправляем письмо на почту.
        try:
            return User.objects.get(email=self.contact)
        except User.DoesNotExist:
            # Отправляем сигнал, который указывает на то, что пользователь
            # пытается добавить другого пользователя не существующего в системе.
            signals.inviting_new_user_by_email.send(
                sender=self.__class__,
                sender_user_id=self.user.id,
                new_user_email=self.contact,
                locale=self.locale,
            )
            raise NotFound(_('Пользователь не найден в системе.'))

    def user_by_phone(self, phone: str) -> User:
        """Аккаунт по номеру телефона."""
        try:
            number = phonenumbers.parse(phone, self.locale.upper())
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError(_('Введен некорректный номер телефона.'))

        formatted_number = phonenumbers.format_number(
            number,
            phonenumbers.PhoneNumberFormat.E164,
        )

        try:
            return User.objects.get(phone=formatted_number)
        except User.DoesNotExist:
            # Отправляем сигнал, который указывает на то, что пользователь
            # пытается добавить другого пользователя не существующего в системе.
            signals.inviting_new_user_by_phone.send(
                sender=self.__class__,
                sender_user_id=self.user.id,
                new_user_phone=formatted_number,
                locale=self.locale,
            )

            raise NotFound(
                _(
                    'Пользователь не найден в системе. Проверьте введенный ' +
                    'номер или воспользуйтесь другими возможностями ' +
                    'добавления друзей.',
                ),
            )


def check_if_exists_fr(validated_data: Dict[str, Account]) -> None:
    """Проверка того, что запрос в друзья уже существует."""
    try:
        friend_request = FriendRequest.objects.get(
            sending_account=validated_data['sending_account'],
            receiving_account=validated_data['receiving_account'],
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


def check_if_reverse_exists_fr(validated_data: Dict[str, Account]) -> None:
    """Проверка того, что обратный запрос в друзья уже существует."""
    try:
        friend_request = FriendRequest.objects.get(
            sending_account=validated_data['receiving_account'],
            receiving_account=validated_data['sending_account'],
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
