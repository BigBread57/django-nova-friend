from rest_framework import mixins
from rest_framework.viewsets import (
    GenericViewSet,
    ModelViewSet,
    ReadOnlyModelViewSet,
)
from rest_framework_extensions.mixins import NestedViewSetMixin
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from nova_friend.services.views import ViewSetSerializerMixin


class BaseReadOnlyViewSet(  # noqa: WPS215
    AutoPermissionViewSetMixin,
    NestedViewSetMixin,
    ViewSetSerializerMixin,
    ReadOnlyModelViewSet,
):
    """Стандартный ReadOnlyViewSet."""

    permission_type_map = {
        **AutoPermissionViewSetMixin.permission_type_map,
        "list": "list",
        "metadata": None,
    }


class BaseRetrieveListCreateUpdateViewSet(  # noqa: WPS215
    ViewSetSerializerMixin,
    AutoPermissionViewSetMixin,
    NestedViewSetMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    """ViewSet с возможностью просмотра/добавления/изменения."""

    permission_type_map = {
        **AutoPermissionViewSetMixin.permission_type_map,
        "list": "list",
        "metadata": None,
    }


class BaseRetrieveListCreateDestroyViewSet(  # noqa: WPS215
    ViewSetSerializerMixin,
    AutoPermissionViewSetMixin,
    NestedViewSetMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    """ViewSet с возможностью просмотра/добавления/удаления."""

    permission_type_map = {
        **AutoPermissionViewSetMixin.permission_type_map,
        'list': 'list',
        'metadata': None,
    }
