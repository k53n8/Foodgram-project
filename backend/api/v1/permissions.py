from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAuthenticatedOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user


class CurrentUserPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'retrieve' and view.kwargs.get('pk') == 'me':
            return request.user and request.user.is_authenticated
        return True
