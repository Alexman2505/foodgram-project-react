from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешаем изменять и удалять объект только его автору,
    для всех остальных доступно лишь чтение."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешаем изменять и удалять данные только админу,
    для всех остальных доступно лишь чтение."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_superuser
