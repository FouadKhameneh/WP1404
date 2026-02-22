from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "name", "resource", "action", "description"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField(read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = ["id", "key", "name", "description", "is_active", "permissions", "permission_ids"]

    def validate_key(self, value):
        if value in {"", None}:
            return None
        return value.lower()

    def get_permissions(self, obj):
        permissions = Permission.objects.filter(permission_roles__role=obj).order_by("code")
        return PermissionSerializer(permissions, many=True).data

    def create(self, validated_data):
        permission_values = validated_data.pop("permission_ids", [])
        role = Role.objects.create(**validated_data)
        self._sync_role_permissions(role, permission_values)
        return role

    def update(self, instance, validated_data):
        permission_values = validated_data.pop("permission_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if permission_values is not None:
            self._sync_role_permissions(instance, permission_values)
        return instance

    def _sync_role_permissions(self, role, permissions):
        RolePermission.objects.filter(role=role).delete()
        role_permissions = [RolePermission(role=role, permission=permission) for permission in permissions]
        if role_permissions:
            RolePermission.objects.bulk_create(role_permissions)


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "phone", "national_id", "full_name"]


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    assigned_by = UserSummarySerializer(read_only=True)

    class Meta:
        model = UserRoleAssignment
        fields = ["id", "role", "assigned_by", "assigned_at"]


class UserRoleAssignmentCreateSerializer(serializers.Serializer):
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), source="role")
