import uuid

import django_filters
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from nova_friend.api.serializers import (
    CreateFriendRequestSerializer,
    FriendRequestSerializer,
)
from nova_friend.models import FriendRequest
from nova_friend.services.action_friend_request import (
    confirm_friend_request,
    friend_request_action,
)
from nova_friend.services.create_friend_request import create_friend_request
from nova_friend.services.enums import FriendRequestAction, FriendRequestStatus
from nova_friend.services.viewsets import BaseRetrieveListCreateDestroyViewSet


class FriendRequestFilter(django_filters.FilterSet):
    """Фильтр для FriendRequest."""

    sending_user_email = django_filters.AllValuesMultipleFilter(
        field_name='sending_user__email',
        label=_(
            'Множественный поиск по email пользователя, ' +
            'запрашивающий добавление в друзья.',
        ),
    )
    sending_user_username = django_filters.AllValuesMultipleFilter(
        field_name='sending_user__username',
        label=_(
            'Множественный поиск по никнейму пользователя, ' +
            'запрашивающий добавление в друзья.',
        ),
    )
    sending_user_first_name = django_filters.AllValuesMultipleFilter(
        field_name='sending_user__first_name ',
        label=_(
            'Множественный поиск по имени пользователя, ' +
            'запрашивающий добавление в друзья.',
        ),
    )
    sending_user_last_name = django_filters.AllValuesMultipleFilter(
        field_name='sending_user__last_name',
        label=_(
            'Множественный поиск по фамилии пользователя, ' +
            'запрашивающий добавление в друзья.',
        ),
    )
    receiving_user_email = django_filters.AllValuesMultipleFilter(
        field_name='receiving_user__email',
        label=_(
            'Множественный поиск по email пользователя, ' +
            'которого добавляют в друзья.',
        ),
    )
    receiving_user_username = django_filters.AllValuesMultipleFilter(
        field_name='receiving_user__username',
        label=_(
            'Множественный поиск по никнейму пользователя, ' +
            'которого добавляют в друзья.',
        ),
    )
    receiving_user_first_name = django_filters.AllValuesMultipleFilter(
        field_name='receiving_user__first_name ',
        label=_(
            'Множественный поиск по имени пользователя, ' +
            'которого добавляют в друзья.',
        ),
    )
    receiving_user_last_name = django_filters.AllValuesMultipleFilter(
        field_name='receiving_user__last_name',
        label=_(
            'Множественный поиск по фамилии пользователя, ' +
            'которого добавляют в друзья.',
        ),
    )

    class Meta(object):
        model = FriendRequest
        fields = (
            'id',
            'sending_user',
            'sending_user_email',
            'sending_user_username',
            'sending_user_first_name',
            'sending_user_last_name',
            'receiving_user',
            'receiving_user_email',
            'receiving_user_username',
            'receiving_user_first_name',
            'receiving_user_last_name',
            'created_at',
            'updated_at',
            'contact',
            'status',
            'token',
        )


class FriendRequestViewSet(BaseRetrieveListCreateDestroyViewSet):
    """Запросы в друзья. Просмотр/создание.

    Стандартные методы:

    1) GET api/friends/friend-request - получение списка запросов в друзья.
    Доступно: всем авторизованным.

    2) GET api/friends/friend-request/<token> - получение конкретного запроса
    по его token.
    Доступно: суперпользователю, отправителю и получателю запроса.

    3) POST api/friends/friend-request - создание запроса в друзья.
    Доступно: всем авторизованным.

    4) DELETE api/friends/friend-request/<token> - удаление запроса в друзья.
    Доступно: суперпользователю, отправителю и получателю запроса.

    Дополнительно:
    - POST api/accounts/friend-request/<token>/confirm -для принятия запроса
    в друзья (доступно суперпользователю и тому, кому отправлен запрос).
    - DELETE api/accounts/friend-request/<token>/reject - удаление запроса в
    друзья (доступно суперпользователю и тому, кому отправлен запрос).
    - DELETE api/accounts/friend-request/<token>/cancel - удаление запроса в
    друзья (доступно суперпользователю и тому, кто отправлен запрос).
    """

    queryset = FriendRequest.objects.select_related(
        'sending__user',
        'receiving_user',
    )
    serializer_class = FriendRequestSerializer
    create_serializer_class = CreateFriendRequestSerializer
    ordering_fields = '__all__'
    search_fields = (
        'sending_user__email',
        'sending_user__username',
        'sending_user__first_name',
        'sending_user__last_name',
        'receiving_user__email',
        'receiving_user__username',
        'receiving_user__first_name',
        'receiving_user__last_name',
    )
    filterset_class = FriendRequestFilter
    permission_type_map = {
        **BaseRetrieveListCreateDestroyViewSet.permission_type_map,
        'confirm': 'confirm',
        'reject': 'reject',
        'cancel': 'cancel',
    }
    lookup_field = 'token'

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
            return FriendRequest.objects.none()

        if user.is_superuser:
            return queryset

        return queryset.filter(
            models.Q(sending_user=user) |
            models.Q(receiving_user=user)
        )

    def perform_create(self, serializer):
        """Создание запроса в друзья."""
        serializer.instance = create_friend_request(
            validated_data=serializer.validated_data,
            sending_user=self.request.user,
            locale=self.request.LANGUAGE_CODE,
        )

    @action(
        methods=['POST'],
        url_path='confirm',
        detail=True,
    )  # type: ignore
    def confirm(self, request: Request, token: uuid.UUID) -> Response:
        """Подтверждение запроса в друзья.

        Формирование url: необходимо передавать token запроса в друзья.

        Данные на вход: отсутствуют.

        Успех:
        Тело - отсутствует.
        Статус - HTTP_200_OK

        Ошибки:

        - При отсутствии token в БД. То есть передан token, не
          существующего запроса.

        Тело: стандартная ошибка о том, что FriendRequest не найден.
        Статус: HTTP_404_NOT_FOUND

        Общее описание: пользователь дает согласие на добавления себя в друзья
        пользователю, который предложил дружбу.
        Отправляется сигнал friend_request_action.

        Доступно: суперпользователю и пользователю, которому был отправлен
        запрос в друзья (получателю).
        """
        friend_request_action(
            status=FriendRequestStatus.CONFIRMED,
            token=token,
        )
        return Response(status=status.HTTP_200_OK)

    @action(
        methods=['DELETE'],
        url_path='reject',
        detail=True,
    )  # type: ignore
    def reject(self, request: Request, token: uuid.UUID) -> Response:
        """Отказаться от запроса в добавления в друзья.

        Формирование url: необходимо передавать token запроса в друзья.

        Данные на вход: отсутствуют.

        Успех:
        Тело - отсутствует.
        Статус - HTTP_204_NO_CONTENT

        Ошибки:

        - При отсутствии token в БД. То есть передан token, не
          существующего запроса.

        Тело: стандартная ошибка о том, что FriendRequest не найден.
        Статус: HTTP_404_NOT_FOUND

        Общее описание: пользователь, получивший запрос на добавление в друзья
        отказывается от дружбы.
        Отправляется сигнал friend_request_action.

        Доступно: суперпользователю и пользователю, которому отправили запрос
        (получателю). Запрос должен иметь статус (FriendRequestStatus.PENDING).
        """
        friend_request_action(
            status=FriendRequestStatus.REJECTED,
            token=token,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['DELETE'],
        url_path='cancel',
        detail=True,
    )  # type: ignore
    def cancel(self, request: Request, token: uuid.UUID) -> Response:
        """Отменить свой запрос на дружбу.

        Формирование url: необходимо передавать token запроса в друзья.

        Данные на вход: отсутствуют.

        Успех:
        Тело - отсутствует.
        Статус - HTTP_204_NO_CONTENT

        Ошибки:

        - При отсутствии token в БД. То есть передан token, не
          существующего запроса.

        Тело: стандартная ошибка о том, что FriendRequest не найден.
        Статус: HTTP_404_NOT_FOUND

        Общее описание: пользователь, создавший запрос на добавление в друзья
        удаляет данный запрос.
        Отправляется сигнал friend_request_action.

        Доступно: суперпользователю и пользователю, который создал запрос
        (отправитель). Запрос должен иметь статус (FriendRequestStatus.PENDING).
        """
        friend_request_action(
            status=FriendRequestStatus.CANCELED,
            token=token,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
