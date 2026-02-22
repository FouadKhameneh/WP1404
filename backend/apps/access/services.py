from apps.access.models import Permission, UserRoleAssignment


def get_user_role_keys(user) -> set[str]:
    if not user or not user.is_authenticated:
        return set()
    values = UserRoleAssignment.objects.filter(
        user=user,
        role__is_active=True,
    ).exclude(
        role__key__isnull=True,
    ).exclude(
        role__key="",
    ).values_list("role__key", flat=True)
    return {value.lower() for value in values}


def user_has_any_role_key(user, role_keys: list[str] | tuple[str, ...] | set[str]) -> bool:
    if user and user.is_superuser:
        return True
    required = {key.lower() for key in role_keys if key}
    if not required:
        return True
    current = get_user_role_keys(user)
    return any(key in current for key in required)


def user_has_permission_codes(
    user,
    permission_codes: list[str] | tuple[str, ...] | set[str],
    match_all: bool = True,
) -> bool:
    if user and user.is_superuser:
        return True
    if not user or not user.is_authenticated:
        return False
    required = {code for code in permission_codes if code}
    if not required:
        return True
    found = set(
        Permission.objects.filter(
            permission_roles__role__user_assignments__user=user,
            permission_roles__role__is_active=True,
            code__in=required,
        ).values_list("code", flat=True)
    )
    if match_all:
        return required.issubset(found)
    return bool(required.intersection(found))


def get_user_permission_codes(user) -> set[str]:
    if user and user.is_superuser:
        return set(
            Permission.objects.values_list("code", flat=True)
        )
    if not user or not user.is_authenticated:
        return set()
    return set(
        Permission.objects.filter(
            permission_roles__role__user_assignments__user=user,
            permission_roles__role__is_active=True,
        )
        .distinct()
        .values_list("code", flat=True)
    )
