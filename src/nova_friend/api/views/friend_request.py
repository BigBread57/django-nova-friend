import uuid

import django_filters
from django.db.models.query_utils import Q  # noqa: WPS347
from nova_target.services.tracking_target.target_engine import target_engine
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from server.apps.nova_account.api.serializers import FriendRequestSerializer
from server.apps.nova_account.api.serializers.friend_request import (
    NewFriendRequestSerializer,
)
from server.apps.nova_account.models import FriendRequest
from server.apps.nova_account.services.enums import FriendRequestStatus
from server.apps.nova_account.services.friend_request.views import (
    cancel_friend_request,
    confirm_friend_request,
    reject_friend_request,
)
from server.apps.services.target_class import ThreeFriendsTargetAction
from server.apps.services.viewsets import RetrieveListCreateViewSet


class FriendRequestFilter(django_filters.FilterSet):
    """Фильтр для FriendRequest."""

    class Meta(object):
        model = FriendRequest
        fields = (
            'id',
            'sending_account',
            'sending_account__user',
            'sending_account__user__email',
            'sending_account__user__username',
            'sending_account__user__first_name',
            'sending_account__user__last_name',
            'receiving_account',
            'receiving_account__user',
            'receiving_account__user__email',
            'receiving_account__user__username',
            'receiving_account__user__first_name',
            'receiving_account__user__last_name',
            'is_approved',
            'created_at',
            'contact',
            'status',
            'token',
        )


class FriendRequestViewSet(RetrieveListCreateViewSet):
    """Запросы в друзья. Просмотр/добавление.

    Стандартные методы:

    1) GET api/accounts/friend-request - получение списка запросов в друзья.
    Доступно: всем авторизованным.

    2) GET api/accounts/friend-request/<token> - получение конкретного запроса
    по его token.
    Доступно: суперпользователю и отправителю и получателю запроса.

    3) POST api/accounts/friend-request - создание запроса в друзья.
    Доступно: всем авторизованным.
    Дополнительно:
    - POST api/accounts/friend-request/<token>/confirm -для принятия запроса
    в друзья (доступно суперпользователю и тому, кому отправлен запрос).

    4) DELETE api/accounts/friend-request/<token> - не доступен.
    Дополнительно:
    - DELETE api/accounts/friend-request/<token>/reject - удаление запроса в
    друзья (доступно суперпользователю и тому, кому отправлен запрос).
    - DELETE api/accounts/friend-request/<token>/cancel - удаление запроса в
    друзья (доступно суперпользователю и тому, кто отправлен запрос).

    5) PATCH, PUT api/accounts/friend-request/<token> - не доступен.
    """

    queryset = FriendRequest.objects.select_related(
        'sending_account__user',
        'receiving_account__user',
    )
    serializer_class = FriendRequestSerializer
    create_serializer_class = NewFriendRequestSerializer
    ordering_fields = '__all__'
    search_fields = (
        'sending_account__user__email',
        'sending_account__user__username',
        'sending_account__user__first_name',
        'sending_account__user__last_name',
        'receiving_account__user__email',
        'receiving_account__user__username',
        'receiving_account__user__first_name',
        'receiving_account__user__last_name',
    )
    filterset_class = FriendRequestFilter
    permission_type_map = {
        **RetrieveListCreateViewSet.permission_type_map,
        'confirm': 'confirm',
        'reject': 'reject',
        'cancel': 'cancel',
    }
    lookup_field = 'token'
    user_for_engine = None

    def get_queryset(self):  # noqa: WPS615
        """Фильтруем выдачу запросов в друзья.

        Суперпользователь видит все запросы в друзья.
        Пользователь видит те запросы в друзья, где он отправитель или
        получатель.
        Остальные ничего не видят.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        return queryset.filter(
            (Q(sending_account=user.account) | Q(receiving_account=user.account)) &  # noqa: E501
            Q(is_approved=False) & Q(status=FriendRequestStatus.PENDING.value),
        )

    @target_engine.register_action(  # type: ignore
        user_argument=0,
        target_class=ThreeFriendsTargetAction,
        user_attribute='user_for_engine',
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

        Доступно: суперпользователю и пользователю, которому был отправлен
        запрос в друзья (получателю).
        """
        friend_request = confirm_friend_request(token=token)
        self.user_for_engine = friend_request.sending_account.user
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
        отказывается от дружбы. При удалении запроса, уведомление, которое
        получает вторая сторона (уведомление о том, что его хотят пригласить в
        друзья), становится не активным, кнопки по данному уведомлению не
        должны быть доступны.

        Доступно: суперпользователю и пользователю, которому отправили запрос
        (получателю). Запрос должен быть активным (is_approved==False).
        """
        reject_friend_request(token=token)
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
        удаляет данный запрос. При удалении запроса, уведомление, которое
        получает вторая сторона (уведомление о том, что его хотят пригласить в
        друзья), становится не активным, кнопки по данному уведомлению не
        должны быть доступны.

        Доступно: суперпользователю и пользователю, который создал запрос
        (отправитель). Запрос должен быть активным (is_approved==False).
        """
        cancel_friend_request(token=token)
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(
        methods=['DELETE'],
        url_path='delete-friend',
        detail=False,
        serializer_class=DeleteFriendSerializer,
    )
    def delete_friend(self, request):
        """Удаление друга из списка друзей.

        Формирование url: автоматическое формирование.

        Данные на вход: {"bad_friend_account_id": int}. Передаем id аккаунта
        пользователя, которого хотим удалить их друзей.

        Успех:
        Тело - отсутствует.
        Статус - HTTP_204_NO_CONTENT

        Ошибки: специфические ошибки отсутствуют.

        Общее описание: пользователь удаляет другого пользователя из своего
        списка друзей.

        Доступно: всем авторизованным.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delete_bad_friend_account(
            user_account=request.user.account,
            bad_friend_account=serializer.validated_data['bad_friend_account_id'],  # noqa: E501
        )

        return Response(status=status.HTTP_204_NO_CONTENT)