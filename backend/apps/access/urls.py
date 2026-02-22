from django.urls import path

from apps.access.views import (
    CurrentAuthorizationAPIView,
    PermissionDetailAPIView,
    PermissionListCreateAPIView,
    RoleDetailAPIView,
    RoleListCreateAPIView,
    UserRoleAssignmentDeleteAPIView,
    UserRoleAssignmentListCreateAPIView,
)

urlpatterns = [
    path("permissions/", PermissionListCreateAPIView.as_view(), name="access-permission-list-create"),
    path("permissions/<int:permission_id>/", PermissionDetailAPIView.as_view(), name="access-permission-detail"),
    path("roles/", RoleListCreateAPIView.as_view(), name="access-role-list-create"),
    path("roles/<int:role_id>/", RoleDetailAPIView.as_view(), name="access-role-detail"),
    path(
        "users/<int:user_id>/roles/",
        UserRoleAssignmentListCreateAPIView.as_view(),
        name="access-user-role-list-create",
    ),
    path(
        "users/<int:user_id>/roles/<int:role_id>/",
        UserRoleAssignmentDeleteAPIView.as_view(),
        name="access-user-role-delete",
    ),
    path("me/authorization/", CurrentAuthorizationAPIView.as_view(), name="access-me-authorization"),
]

