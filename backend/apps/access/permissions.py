from rest_framework.permissions import BasePermission

from apps.access.services import user_has_any_role_key, user_has_permission_codes


class HasRBACPermissions(BasePermission):
    message = "Missing required role permissions."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        method_codes = getattr(view, "permission_codes_by_method", {})
        required = method_codes.get(request.method.upper(), getattr(view, "required_permission_codes", []))
        return user_has_permission_codes(request.user, required, match_all=True)


class HasRoleKeys(BasePermission):
    message = "Role policy requirements were not satisfied."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        method_keys = getattr(view, "role_keys_by_method", {})
        required = method_keys.get(request.method.upper(), getattr(view, "required_role_keys", []))
        return user_has_any_role_key(request.user, required)
