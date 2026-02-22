from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from apps.access.models import Permission, Role, UserRoleAssignment
from apps.access.serializers import (
    PermissionSerializer,
    RoleSerializer,
    UserRoleAssignmentCreateSerializer,
    UserRoleAssignmentSerializer,
    UserSummarySerializer,
)
from apps.identity.services import error_response, success_response


class PermissionListCreateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        permissions = Permission.objects.order_by("resource", "action", "code")
        serializer = PermissionSerializer(permissions, many=True)
        return success_response({"results": serializer.data}, status_code=status.HTTP_200_OK)

    def post(self, request):
        serializer = PermissionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        permission = serializer.save()
        response_serializer = PermissionSerializer(permission)
        return success_response(response_serializer.data, status_code=status.HTTP_201_CREATED)


class PermissionDetailAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, permission_id):
        permission = get_object_or_404(Permission, id=permission_id)
        serializer = PermissionSerializer(permission)
        return success_response(serializer.data, status_code=status.HTTP_200_OK)

    def patch(self, request, permission_id):
        permission = get_object_or_404(Permission, id=permission_id)
        serializer = PermissionSerializer(permission, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        updated_permission = serializer.save()
        response_serializer = PermissionSerializer(updated_permission)
        return success_response(response_serializer.data, status_code=status.HTTP_200_OK)

    def delete(self, request, permission_id):
        permission = get_object_or_404(Permission, id=permission_id)
        permission.delete()
        return success_response({"message": "Permission deleted successfully."}, status_code=status.HTTP_200_OK)


class RoleListCreateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        roles = Role.objects.order_by("name")
        serializer = RoleSerializer(roles, many=True)
        return success_response({"results": serializer.data}, status_code=status.HTTP_200_OK)

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        role = serializer.save()
        response_serializer = RoleSerializer(role)
        return success_response(response_serializer.data, status_code=status.HTTP_201_CREATED)


class RoleDetailAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, role_id):
        role = get_object_or_404(Role, id=role_id)
        serializer = RoleSerializer(role)
        return success_response(serializer.data, status_code=status.HTTP_200_OK)

    def patch(self, request, role_id):
        role = get_object_or_404(Role, id=role_id)
        serializer = RoleSerializer(role, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        updated_role = serializer.save()
        response_serializer = RoleSerializer(updated_role)
        return success_response(response_serializer.data, status_code=status.HTTP_200_OK)

    def delete(self, request, role_id):
        role = get_object_or_404(Role, id=role_id)
        role.delete()
        return success_response({"message": "Role deleted successfully."}, status_code=status.HTTP_200_OK)


class UserRoleAssignmentListCreateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        user = get_object_or_404(get_user_model(), id=user_id)
        assignments = (
            UserRoleAssignment.objects.filter(user=user)
            .select_related("assigned_by", "role")
            .order_by("assigned_at")
        )
        serializer = UserRoleAssignmentSerializer(assignments, many=True)
        return success_response(
            {"user": UserSummarySerializer(user).data, "roles": serializer.data},
            status_code=status.HTTP_200_OK,
        )

    def post(self, request, user_id):
        user = get_object_or_404(get_user_model(), id=user_id)
        serializer = UserRoleAssignmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        role = serializer.validated_data["role"]
        assignment, created = UserRoleAssignment.objects.get_or_create(
            user=user,
            role=role,
            defaults={"assigned_by": request.user},
        )
        if not created:
            return error_response(
                code="ROLE_ALREADY_ASSIGNED",
                message="This role is already assigned to the user.",
                details={},
                status_code=status.HTTP_409_CONFLICT,
            )

        response_serializer = UserRoleAssignmentSerializer(assignment)
        return success_response(response_serializer.data, status_code=status.HTTP_201_CREATED)


class UserRoleAssignmentDeleteAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def delete(self, request, user_id, role_id):
        user = get_object_or_404(get_user_model(), id=user_id)
        role = get_object_or_404(Role, id=role_id)
        assignment = get_object_or_404(UserRoleAssignment, user=user, role=role)
        assignment.delete()
        return success_response(
            {"message": "Role assignment removed successfully."},
            status_code=status.HTTP_200_OK,
        )


class CurrentAuthorizationAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        assignments = UserRoleAssignment.objects.filter(user=request.user).select_related("role")
        roles = Role.objects.filter(id__in=assignments.values_list("role_id", flat=True)).order_by("name")
        role_data = RoleSerializer(roles, many=True).data
        permissions = Permission.objects.filter(
            permission_roles__role_id__in=assignments.values_list("role_id", flat=True)
        ).distinct().order_by("resource", "action", "code")
        permission_data = PermissionSerializer(permissions, many=True).data
        return success_response(
            {
                "user": UserSummarySerializer(request.user).data,
                "roles": role_data,
                "permissions": permission_data,
            },
            status_code=status.HTTP_200_OK,
        )
