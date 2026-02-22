from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from apps.access.models import UserRoleAssignment


class PermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source="content_type.app_label", read_only=True)
    model = serializers.CharField(source="content_type.model", read_only=True)

    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "app_label", "model"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        write_only=True,
        required=False,
        source="permissions",
    )

    class Meta:
        model = Group
        fields = ["id", "name", "permissions", "permission_ids"]


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
    role_id = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), source="role")
