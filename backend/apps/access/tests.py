from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment


class AccessAuthorizationApiTests(APITestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin01",
            email="admin01@example.com",
            password="StrongPass123!",
            phone="09120001001",
            national_id="1000000001",
            full_name="Admin User",
        )
        self.user = get_user_model().objects.create_user(
            username="detective02",
            email="detective02@example.com",
            password="StrongPass123!",
            phone="09120001002",
            national_id="1000000002",
            full_name="Detective Two",
        )
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.user_token = Token.objects.create(user=self.user)
        self.permissions_url = "/api/v1/access/permissions/"
        self.roles_url = "/api/v1/access/roles/"
        self.user_roles_url = f"/api/v1/access/users/{self.user.id}/roles/"
        self.me_authorization_url = "/api/v1/access/me/authorization/"
        self.sample_permission = Permission.objects.create(
            code="cases.create",
            name="Create Case",
            resource="cases",
            action="create",
            description="Can create a case",
        )

    def test_admin_can_list_permissions(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        response = self.client.get(self.permissions_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        results = response.data["data"]["results"]
        self.assertGreaterEqual(len(results), 1)
        codes = [p["code"] for p in results]
        self.assertIn(self.sample_permission.code, codes)

    def test_admin_can_create_update_and_delete_permission(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        create_payload = {
            "code": "cases.close",
            "name": "Close Case",
            "resource": "cases",
            "action": "close",
            "description": "Can close a case",
        }

        create_response = self.client.post(self.permissions_url, create_payload, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(create_response.data["success"])
        permission_id = create_response.data["data"]["id"]

        patch_response = self.client.patch(
            f"/api/v1/access/permissions/{permission_id}/",
            {"description": "Updated permission description"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertTrue(patch_response.data["success"])
        self.assertEqual(patch_response.data["data"]["description"], "Updated permission description")

        delete_response = self.client.delete(f"/api/v1/access/permissions/{permission_id}/", format="json")
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Permission.objects.filter(id=permission_id).exists())

    def test_non_admin_cannot_list_permissions(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.user_token.key}")

        response = self.client.get(self.permissions_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "FORBIDDEN")

    def test_admin_can_create_role_and_assign_permission(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        payload = {
            "name": "DetectiveRole",
            "description": "Detective role",
            "permission_ids": [self.sample_permission.id],
        }

        response = self.client.post(self.roles_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["name"], "DetectiveRole")
        self.assertEqual(len(response.data["data"]["permissions"]), 1)
        role = Role.objects.get(name="DetectiveRole")
        self.assertTrue(RolePermission.objects.filter(role=role, permission=self.sample_permission).exists())

    def test_admin_can_update_and_delete_role(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        role = Role.objects.create(name="SergeantRole")
        Permission.objects.create(
            code="cases.review",
            name="Review Case",
            resource="cases",
            action="review",
            description="Can review a case",
        )
        new_permission = Permission.objects.get(code="cases.review")
        patch_payload = {"description": "Updated", "permission_ids": [new_permission.id]}

        patch_response = self.client.patch(f"/api/v1/access/roles/{role.id}/", patch_payload, format="json")

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertTrue(patch_response.data["success"])
        self.assertEqual(patch_response.data["data"]["description"], "Updated")
        self.assertEqual(len(patch_response.data["data"]["permissions"]), 1)

        delete_response = self.client.delete(f"/api/v1/access/roles/{role.id}/", format="json")
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Role.objects.filter(id=role.id).exists())

    def test_admin_can_assign_and_remove_user_role(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        role = Role.objects.create(name="OfficerRole")
        assign_payload = {"role_id": role.id}

        assign_response = self.client.post(self.user_roles_url, assign_payload, format="json")
        self.assertEqual(assign_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(assign_response.data["success"])

        delete_response = self.client.delete(
            f"/api/v1/access/users/{self.user.id}/roles/{role.id}/",
            format="json",
        )
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertTrue(delete_response.data["success"])
        self.assertFalse(UserRoleAssignment.objects.filter(user=self.user, role=role).exists())

    def test_assigning_duplicate_role_returns_conflict(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        role = Role.objects.create(name="CaptainRole")
        payload = {"role_id": role.id}

        first_response = self.client.post(self.user_roles_url, payload, format="json")
        second_response = self.client.post(self.user_roles_url, payload, format="json")

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(second_response.data["success"])
        self.assertEqual(second_response.data["error"]["code"], "ROLE_ALREADY_ASSIGNED")

    def test_current_authorization_returns_roles_and_permissions(self):
        role = Role.objects.create(name="CaptainRole")
        RolePermission.objects.create(role=role, permission=self.sample_permission)
        UserRoleAssignment.objects.create(user=self.user, role=role, assigned_by=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.user_token.key}")

        response = self.client.get(self.me_authorization_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["id"], self.user.id)
        self.assertEqual(len(response.data["data"]["roles"]), 1)
        self.assertEqual(len(response.data["data"]["permissions"]), 1)
