import rules
from rules.predicates import is_authenticated, is_superuser

from nova_friend.services.enums import FriendRequestStatus


@rules.predicate
def is_receiving_user(user, friend_request):
    """Пользователь, которого добавляют в друзья."""
    return user == friend_request.receiving_user


@rules.predicate
def is_sending_user(user, friend_request):
    """Пользователь, запрашивающий добавление в друзья."""
    return user == friend_request.sending_user


view_friend_request = is_superuser | is_receiving_user | is_sending_user
confirm_reject_friend_request = is_superuser | is_receiving_user
cancel_friend_request = is_superuser | is_sending_user
delete_friend_request = is_superuser | is_sending_user


@rules.predicate
def has_view_friend_request(user, friend_request):
    """Права на просмотр запросов в друзья."""
    return view_friend_request(user, friend_request)


@rules.predicate
def has_confirm_friend_request(user, friend_request):
    """Права на согласие принятие дружбы."""
    if friend_request.status == FriendRequestStatus.PENDING:
        return confirm_reject_friend_request(user, friend_request)
    return False


@rules.predicate
def has_reject_friend_request(user, friend_request):
    """Права на отказ от дружбы со стороны получателя."""
    if friend_request.status != FriendRequestStatus.CONFIRMED:
        return confirm_reject_friend_request(user, friend_request)
    return False


@rules.predicate
def has_cancel_friend_request(user, friend_request):
    """Права на отказ от дружбы со стороны отправителя."""
    if friend_request.status != FriendRequestStatus.CONFIRMED:
        return cancel_friend_request(user, friend_request)
    return False


@rules.predicate
def has_delete_friend_request(user, friend_request):
    """Права на удаление запроса."""
    if friend_request.status == FriendRequestStatus.CONFIRMED:
        return delete_friend_request(user, friend_request)
    return False


rules.set_perm('nova_account.view_friendrequest', has_view_friend_request)
rules.set_perm('nova_account.add_friendrequest', is_authenticated)
rules.set_perm('nova_account.confirm_friendrequest', has_confirm_friend_request)
rules.set_perm('nova_account.reject_friendrequest', has_reject_friend_request)
rules.set_perm('nova_account.cancel_friendrequest', has_cancel_friend_request)
rules.set_perm('nova_account.delete_friendrequest', has_delete_friend_request)
rules.set_perm('nova_account.list_friendrequest', is_authenticated)
