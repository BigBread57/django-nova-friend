from django import dispatch

# Определяем сигнал, который срабатывает в момент попытки добавления не
# существующего пользователя по email.
inviting_new_user_by_email = dispatch.Signal()

# Определяем сигнал, который срабатывает в момент попытки добавления не
# существующего пользователя по телефону.
inviting_new_user_by_phone = dispatch.Signal()
