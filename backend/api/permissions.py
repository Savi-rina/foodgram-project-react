from rest_framework import permissions


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """Проверка, что пользователь является админом, автором
        или применен безопасный метод."""
    def has_permission(self, request, view):
        return (request.user.is_authenticated or request.method in
                permissions.SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS or (
                    request.user == obj.author) or request.user.is_staff)
    