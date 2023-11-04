import django_filters
from django.utils.translation import gettext_lazy as _

from nova_friend.api.serializers import (
    ReferralCodeSerializer,
    ReferralInviteSerializer,
)
from nova_friend.api.serializers.referral_code import (
    CreateReferralCodeSerializer,
    UpdateReferralCodeSerializer,
)
from nova_friend.models import ReferralCode
from nova_friend.services.create_referral_code import create_referral_code
from nova_friend.services.viewsets import BaseRetrieveListCreateUpdateViewSet


class ReferralCodeFilter(django_filters.FilterSet):
    """Фильтр для ReferralCode."""

    user_email = django_filters.AllValuesMultipleFilter(
        field_name='user__email',
        label=_(
            'Множественный поиск по email пользователя, ' +
            'который владеет реферальным кодом.',
        ),
    )
    user_username = django_filters.AllValuesMultipleFilter(
        field_name='user__username',
        label=_(
            'Множественный поиск по никнейму пользователя, ' +
            'который владеет реферальным кодом.',
        ),
    )
    user_first_name = django_filters.AllValuesMultipleFilter(
        field_name='user__first_name ',
        label=_(
            'Множественный поиск по имени пользователя, ' +
            'который владеет реферальным кодом.',
        ),
    )
    user_last_name = django_filters.AllValuesMultipleFilter(
        field_name='user__last_name',
        label=_(
            'Множественный поиск по фамилии пользователя, ' +
            'который владеет реферальным кодом.',
        ),
    )

    class Meta(object):
        model = ReferralCode
        fields = (
            'id',
            'user',
            'user_email',
            'user_username',
            'user_first_name',
            'user_last_name',
            'code',
        )


class ReferralCodeViewSet(BaseRetrieveListCreateUpdateViewSet):
    """Реферальный код. Просмотр/изменение/удаление.

    Стандартные методы:

    1) GET api/friends/referral-code - получение списка реферальных кодов.
    Доступно: всем авторизованным.

    2) GET api/friends/referral-code/<id> - получение конкретного
    реферального кода по его id.
    Доступно: всем авторизованным.

    3) POST api/friends/referral-code - создание реферального кода .

    4) DELETE api/friends/referral-code/<id> - не доступен.

    5) PATCH, PUT api/friends/referral-code/<id> - изменение реферального кода.
    """

    queryset = ReferralCode.objects.select_related('user')
    serializer_class = ReferralCodeSerializer
    create_serializer_class = CreateReferralCodeSerializer
    update_serializer_class = UpdateReferralCodeSerializer
    ordering_fields = '__all__'
    search_fields = (
        'user__email',
        'user__username',
        'user__first_name',
        'user__last_name',
        'code',
        'note',
    )
    filterset_class = ReferralCodeFilter

    def get_queryset(self):  # noqa: WPS615
        """Фильтруем выдачу запросов в друзья.

        Суперпользователь видит все запросы в друзья.
        Пользователь видит те запросы в друзья, где он отправитель или
        получатель.
        Остальные ничего не видят.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if getattr(self, "swagger_fake_view", False):
            return ReferralCode.objects.none()

        if user.is_superuser:
            return queryset

        return queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        serializer.instance = create_referral_code(
            validated_data=serializer.validated_data
        )
