from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to users with role='admin'."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.role == 'admin')


class IsTeamMember(BasePermission):
    """Allow access only to members of the team being accessed."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        # obj is a Team document
        member_ids = [str(m.id) for m in obj.members]
        return str(user.id) == str(obj.owner.id) or str(user.id) in member_ids
