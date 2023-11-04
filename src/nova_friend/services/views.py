import uuid
from typing import Optional, Type

from rest_framework.exceptions import NotFound
from rest_framework.serializers import Serializer

from server.apps.nova_account.models import FriendRequest
from server.apps.nova_account.services.enums import FriendRequestStatus
from server.apps.nova_notification.models import Notification
from server.apps.nova_notification.models.notification import TypeNotification


class ViewSetSerializerMixin:  # noqa: WPS306, WPS338
    """Миксин позволяет не переопределять get_serializer_class().

    В ViesSet можно сразу указать нужный сериалайзер для action.
    Serializer_class - для GET (получение объекта).
    Create_serializer_class - для POST.
    Update_serializer_class - для PUT, PATCH.
    list_serializer_class - для GET (получение списка).
    """

    create_serializer_class: Optional[Serializer] = None
    update_serializer_class: Optional[Serializer] = None
    list_serializer_class: Optional[Serializer] = None

    def _get_serializer_class(
        self,
        *args,
        **kwargs,
    ) -> Optional[Type[Serializer]]:
        """Каждый action обладает собственным сериалазйером.

        Можно указывать во ViewSet.
        """
        if self.action == 'create':  # type: ignore
            return self.create_serializer_class
        if self.action in {'update', 'partial_update'}:  # type: ignore
            return self.update_serializer_class or self.create_serializer_class
        if self.action == 'list':  # type: ignore
            return self.list_serializer_class
        return None

    def get_serializer_class(self) -> Type[Serializer]:
        """Возвращаем класс сериалайзера с учетом action."""
        serializer_class = self._get_serializer_class()
        if serializer_class:
            return serializer_class
        return super().get_serializer_class()  # type: ignore
