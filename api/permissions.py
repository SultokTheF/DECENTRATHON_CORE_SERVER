from rest_framework import permissions

class IsStaffForCenter(permissions.BasePermission):
    """
    Пользователь с ролью STAFF может управлять только секциями и расписанием своего центра.
    """

    def has_object_permission(self, request, view, obj):
        # Если пользователь является суперпользователем (админом), предоставить все права
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Если пользователь STAFF, проверить, привязан ли он к центру
        if request.user.role == 'STAFF':
            return obj.center.users.filter(id=request.user.id).exists()

        return False