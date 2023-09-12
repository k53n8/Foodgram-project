from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAuthenticatedOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user


class CustomUserPermissions(BasePermission):
    """
    Разрешение, которое позволяет только аутентифицированным пользователям
    получить доступ к эндпоинту 'me', а всем пользователям - к эндпоинтам
    'users' и 'users/<id>/'.
    """
    def has_permission(self, request, view):
        if view.action == 'me':
            return request.user and request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS
