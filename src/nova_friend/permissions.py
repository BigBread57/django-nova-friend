import rules
from django.apps import apps

from nova_friend.apps import NovaFriendConfig

actions = ['view', 'add', 'change', 'delete', 'list']
name_models = apps.all_models[NovaFriendConfig.name]

nova_friend_permission = {
    '{0}.{1}_{2}'.format(NovaFriendConfig.name, action, name_model)
    for action in actions
    for name_model in name_models
}

if not rules.permissions.permissions:
    # Устанавливаем доступ для всех и во всех представлениях.
    for keys in nova_friend_permission:
        rules.set_perm(keys, rules.always_allow)
