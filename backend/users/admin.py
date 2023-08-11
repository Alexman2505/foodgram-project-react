from django.contrib import admin
from users.models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Управление пользователями в admin."""
    fields = ('username', 'email', 'first_name', 'last_name', 'password')
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email',)
    list_filter = ('username', 'email',)
    empty_value_display = '-пусто-'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Управление подписками в admin."""

    list_display = ('id', 'user', 'author')
    search_fields = ('user', 'author')
    empty_value_display = '-пусто-'
