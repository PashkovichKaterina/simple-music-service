from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        params = request.resolver_match.kwargs
        user_id = int(params["users_pk"]) if "users_pk" in params.keys() else int(params["pk"])
        return user_id == request.user.id
