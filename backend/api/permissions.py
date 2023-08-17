from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """Разрешаем изменять и удалять объект только его автору,
    для всех остальных доступно лишь чтение."""

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.method in SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Разрешаем изменять и удалять данные только админу,
    для всех остальных доступно лишь чтение."""

    def has_permission(self, request, view):
        return (
            True
            if request.method in SAFE_METHODS
            else request.user and request.user.is_superuser
        )
