from django.contrib.admin import ModelAdmin, register

from users.models import Subscription, User


@register(User)
class UserAdmin(ModelAdmin):
    """Управление пользователями в админке."""

    fields = ('username', 'email', 'first_name', 'last_name', 'password')
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    search_fields = (
        'username',
        'email',
    )
    list_filter = (
        'username',
        'email',
    )
    empty_value_display = '-пусто-'


@register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    """Управление подписками в админке."""

    list_display = ('id', 'user', 'author')
    search_fields = ('user', 'author')
    empty_value_display = '-пусто-'
