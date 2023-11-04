import re

import phonenumbers
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from phonenumber_field.validators import validate_international_phonenumber
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, ValidationError

from nova_friend import signals

User = get_user_model()


def get_referral_link(user_email: str) -> str:
    """Ссылка с referral для понимания того, кто пригласил пользователя."""
    domain_name = settings.DOMAIN_NAME  # type: ignore
    # FIXME
    return f'https://{domain_name}/referral-invite/?user_email={user_email}'


class LinkFormation(APIException):
    """Вызов исключения во время создания FriendRequest по link."""

    status_code = status.HTTP_204_NO_CONTENT
    default_detail = _('Формирование ссылки.')
    default_code = 'link_formation'


class Receiver(object):
    """Класс для получения корректного receiver для запроса в друзья."""

    def __init__(  # noqa: WPS211
        self,
        contact: str,
        sending_user: User,
        locale: str,
    ):
        """Установка переменных."""
        self.contact = contact
        self.sending_user = sending_user
        self.locale = locale

    def receiving_user_by_contact(self) -> User:  # noqa: C901
        """Получатель запроса на дружбу по строке contact."""
        # Получаем ключевое слово link для формирования ссылки.
        # В таком случае мы не создаем FriendRequest, а вызываем исключение
        # с необходимой информацией.
        if self.contact == 'referral_link':
            raise LinkFormation(
                {
                    'referral_link': get_referral_link(self.sending_user.email),
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
                sending_user_id=self.sending_user.id,
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
                sending_user_id=self.sending_user.id,
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
