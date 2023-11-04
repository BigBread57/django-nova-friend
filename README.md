# Django Nova Friend
A short description of the project.

## Установка

### 1. Добавь репозиторий

Проект хранится в репозитории `pypi.letsnova.ru`, поэтому его сначала
нужно добавить в список репозиториев.

Для `poetry` это делается в файле `pyproject.toml`:

```toml
[[tool.poetry.source]]
name = "nova"
url = "https://pypi.letsnova.ru/simple/"
primary = "default"
```

### 2. Установи пакет

```shell
poetry add django-nova-friend
```

### 3. Добавь его в INSTALLED_APPS

```python
INSTALLED_APPS = [
  ...,
  'nova_friend',
]
```

### 4. подключи API в любом файле urls.py

```python
from django.urls import include, path
from nova_friend.api.routers import router

urlpatterns = [
  ...,
  path('api/', include(router.urls)),
]
```


### Сигналы
1) inviting_new_user_by_email - Сигнал срабатывает, когда пользователь пытается 
отправить приглашение другому пользователю, которого не существует в системе.
Сигнал отправляет следующую информацию:
- new_user_email (str): email нового пользователя;
- sending_user_email (str): email отправителя запроса;
- locale (str): локаль, с которой был отправлен запрос.


Пример обработки сигнала
```python
class LimitExceeded(APIException):
    """Вызов исключения во время создания FriendRequest по link."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Превышен лимит приглашений друзей в ближний круг.')
    default_code = 'limit_exceeded'


@receiver(inviting_new_user_by_email)
def send_email_for_new_user(
    sender,
    sending_user_id: int,
    new_user_email: str,
    locale: str,
    **kwarg,
):
    """Отправка письма пользователю, которого нет в системе."""
    # Получаем настройки пользователя. Проверяем количество попыток.
    # Если попытки еще есть, то разрешаем отправку приглашения.
    # Иначе вызываем исключение.
    customization = Customization.objects.get(
        account_id=self.request_user_account_id,
    )
    if customization.number_invites >= settings.MAX_NUMBER_INVITES:  # type: ignore  # noqa: E501
        raise LimitExceeded
    
    sending_user = User.objects.get(id=sending_user_id)
    # Формируем данные для отправки письма.
    name_template = f'send_email_friend_request/{locale}.html'
    translation.activate(locale)
    context = {
        'sender_full_name': self.request_full_name,
        'url': get_link_with_referral(self.request_user_email),
        'year': datetime.today().year,
        'company_name': 'Nova',
    }
    template = get_template(name_template).render(context)

    # Передаем message=None, потому что это HTML-письмо.
    send_mail(
        subject=_('Вас приглашают в Nova Health!'),
        message=None,  # type: ignore
        from_email=None,
        recipient_list=[self.contact],
        fail_silently=False,
        html_message=template,
    )

    # Увеличиваем счетчик приглашений.
    customization.number_invites += 1
    customization.save(update_fields=['number_invites'])

    raise NotFound(
        _(
            'Пользователь не найден в системе. ' +
            'По указанному адресу отправлено приглашение!',
        ),
    )
```

2) inviting_new_user_by_phone - Сигнал срабатывает, когда пользователь пытается 
отправить приглашение другому пользователю, которого не существует в системе.
Сигнал отправляет следующую информацию:
- new_user_email (str): email нового пользователя;
- sending_user_email (str): email отправителя запроса;
- locale (str): локаль, с которой был отправлен запрос.