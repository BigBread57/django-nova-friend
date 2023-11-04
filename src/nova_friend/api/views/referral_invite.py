import django_filters
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from nova_friend.api.serializers import ReferralInviteSerializer
from nova_friend.models import ReferralInvite
from nova_friend.services.viewsets import BaseReadOnlyViewSet


class ReferralInviteFilter(django_filters.FilterSet):
    """Фильтр для ReferralInvite."""

    referral_user_email = django_filters.AllValuesMultipleFilter(
        field_name='referral_user__email',
        label=_(
            'Множественный поиск по email пользователя, ' +
            'который пригласил.',
        ),
    )
    referral_user_username = django_filters.AllValuesMultipleFilter(
        field_name='referral_user__username',
        label=_(
            'Множественный поиск по никнейму пользователя, ' +
            'который пригласил.',
        ),
    )
    referral_user_first_name = django_filters.AllValuesMultipleFilter(
        field_name='referral_user__first_name ',
        label=_(
            'Множественный поиск по имени пользователя, ' +
            'который пригласил.',
        ),
    )
    referral_user_last_name = django_filters.AllValuesMultipleFilter(
        field_name='referral_user__last_name',
        label=_(
            'Множественный поиск по фамилии пользователя, ' +
            'который пригласил.',
        ),
    )
    invited_user_email = django_filters.AllValuesMultipleFilter(
        field_name='invited_user__email',
        label=_(
            'Множественный поиск по email пользователя, ' +
            'который был приглашен.',
        ),
    )
    invited_user_username = django_filters.AllValuesMultipleFilter(
        field_name='invited_user__username',
        label=_(
            'Множественный поиск по никнейму пользователя, ' +
            'который был приглашен.',
        ),
    )
    invited_user_first_name = django_filters.AllValuesMultipleFilter(
        field_name='invited_user__first_name ',
        label=_(
            'Множественный поиск по имени пользователя, ' +
            'который был приглашен.',
        ),
    )
    invited_user_last_name = django_filters.AllValuesMultipleFilter(
        field_name='invited_user__last_name',
        label=_(
            'Множественный поиск по фамилии пользователя, ' +
            'который был приглашен.',
        ),
    )
    referral_code_code = django_filters.AllValuesMultipleFilter(
        field_name='referral_code__code',
        label=_('Множественный поиск по реферальному коду.'),
    )

    class Meta(object):
        model = ReferralInvite
        fields = (
            'id',
            'referral_user',
            'referral_user_email',
            'referral_user_username',
            'referral_user_first_name',
            'referral_user_last_name',
            'invited_user',
            'invited_user_email',
            'invited_user_username',
            'invited_user_first_name',
            'invited_user_last_name',
            'referral_code',
            'referral_code_code',
        )


class ReferralInviteViewSet(BaseReadOnlyViewSet):
    """Приглашенные по реферальной системе. Просмотр.

    Стандартные методы:

    1) GET api/friends/referral-invite - получение списка людей, которые были
    вами приглашены.
    Доступно: всем авторизованным.

    2) GET api/friends/referral-invite/id - получение конкретного
    приглашенного человека по его id.
    Доступно: суперпользователю, отправителю и получателю запроса.
    """

    queryset = ReferralInvite.objects.select_related(
        'referral_user',
        'invited_user',
        'referral_code',
    )
    serializer_class = ReferralInviteSerializer
    ordering_fields = '__all__'
    search_fields = (
        'referral_user__email',
        'referral_user__username',
        'referral_user__first_name',
        'referral_user__last_name',
        'invited_user__email',
        'invited_user__username',
        'invited_user__first_name',
        'invited_user__last_name',
        'referral_code__code',
    )
    filterset_class = ReferralInviteFilter

    def get_queryset(self):  # noqa: WPS615
        """Фильтруем выдачу людей, приглашенных по реферальной системе.

        Суперпользователь видит всех приглашенных.
        Пользователь видит тех пользователей, которых пригласил.
        Остальные ничего не видят.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if getattr(self, "swagger_fake_view", False):
            return ReferralInvite.objects.none()

        if user.is_superuser:
            return queryset

        return queryset.filter(referral_user=user)

    @action(
        methods=['GET'],
        url_path='my-referral-user',
        detail=False,
    )  # type: ignore
    def my_referral_user(self, request: Request) -> Response:
        """Получить пользователя, который пригласил вас в систему.

        Формирование url: автоматическое формирование

        Данные на вход: отсутствуют.

        Успех:
        Тело - информация о пользователе, который вас пригласил.
        Статус - HTTP_200_OK

        Ошибки: специфические ошибки отсутствуют.

        Общее описание: пользователь получает информацию о пользователе,
        который пригласил его в систему.

        Доступно: всем авторизованным.
        """
        referral_user = ReferralInvite.objects.get(
            invited_user=request.user
        )
        return Response(
            data=BaseInfoUserSerializer(referral_user).data,
            status=status.HTTP_200_OK,

        )
