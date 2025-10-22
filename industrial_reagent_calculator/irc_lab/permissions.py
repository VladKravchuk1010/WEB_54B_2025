from rest_framework import permissions

class IsManager(permissions.BasePermission):
    """Проверяет, является ли пользователь менеджером (is_staff)"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

class IsAdmin(permissions.BasePermission):
    """Проверяет, является ли пользователь администратором (is_superuser)"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)

class IsOwner(permissions.BasePermission):
    """Проверяет, является ли пользователь владельцем объекта"""
    def has_object_permission(self, request, view, obj):
        # Для заявок - проверяем что пользователь является создателем
        if hasattr(obj, 'client'):
            return obj.client == request.user
        return False

class IsOwnerOrManager(permissions.BasePermission):
    """Проверяет, является ли пользователь владельцем ИЛИ менеджером"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        if hasattr(obj, 'client'):
            return obj.client == request.user
        return False