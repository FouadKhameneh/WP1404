
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.investigation.models import ReasoningApproval, ReasoningSubmission


class InvestigationAuthorizationPolicyTests(APITestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin02",
            email="admin02@example.com",
            password="StrongPass123!",
            phone="09120002001",
            national_id="2000000001",
            full_name="Admin User Two",
        )
        self.detective_user = get_user_model().objects.create_user(
            username="detective03",
            email="detective03@example.com",
            password="StrongPass123!",
            phone="09120002002",
            national_id="2000000002",
            full_name="Detective Three",
        )
        self.sergeant_user = get_user_model().objects.create_user(
            username="sergeant01",
            email="sergeant01@example.com",
            password="StrongPass123!",
            phone="09120002003",
            national_id="2000000003",
            full_name="Sergeant One",
        )
        self.officer_user = get_user_model().objects.create_user(
            username="officer03",
            email="officer03@example.com",
            password="StrongPass123!",
            phone="09120002004",
            national_id="2000000004",
            full_name="Officer Three",
        )

        self.detective_token = Token.objects.create(user=self.detective_user)
        self.sergeant_token = Token.objects.create(user=self.sergeant_user)
        self.officer_token = Token.objects.create(user=self.officer_user)

        self.permission_view = Permission.objects.create(
            code="investigation.reasoning.view",
            name="View Reasoning",
            resource="investigation.reasoning",
            action="view",
            description="Can view reasoning submissions",
        )
        self.permission_submit = Permission.objects.create(
            code="investigation.reasoning.submit",
            name="Submit Reasoning",
            resource="investigation.reasoning",
            action="submit",
            description="Can submit detective reasoning",
        )
        self.permission_approve = Permission.objects.create(
            code="investigation.reasoning.approve",
            name="Approve Reasoning",
            resource="investigation.reasoning",
            action="approve",
            description="Can approve or reject detective reasoning",
        )

        self.role_detective = Role.objects.create(key="detective", name="Detective")
        self.role_sergeant = Role.objects.create(key="sergeant", name="Sergeant")
        self.role_officer = Role.objects.create(key="officer", name="Officer")

        RolePermission.objects.create(role=self.role_detective, permission=self.permission_view)
        RolePermission.objects.create(role=self.role_detective, permission=self.permission_submit)
        RolePermission.objects.create(role=self.role_sergeant, permission=self.permission_view)
        RolePermission.objects.create(role=self.role_sergeant, permission=self.permission_approve)

        UserRoleAssignment.objects.create(user=self.detective_user, role=self.role_detective, assigned_by=self.admin_user)
        UserRoleAssignment.objects.create(user=self.sergeant_user, role=self.role_sergeant, assigned_by=self.admin_user)
        UserRoleAssignment.objects.create(user=self.officer_user, role=self.role_officer, assigned_by=self.admin_user)

        self.reasonings_url = "/api/v1/investigation/reasonings/"

    def test_detective_can_submit_reasoning(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.detective_token.key}")
        payload = {
            "case_reference": "CASE-1001",
            "title": "Linking witness testimony",
            "narrative": "This narrative ties evidence A and B.",
        }

        response = self.client.post(self.reasonings_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], "pending")

    def test_user_without_required_permission_cannot_submit_reasoning(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.officer_token.key}")
        payload = {
            "case_reference": "CASE-1002",
            "title": "Officer attempt",
            "narrative": "Should be blocked by RBAC permission check.",
        }

        response = self.client.post(self.reasonings_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "FORBIDDEN")

    def test_sergeant_can_approve_detective_reasoning(self):
        reasoning = ReasoningSubmission.objects.create(
            case_reference="CASE-1003",
            title="Detective submission",
            narrative="Pending detective reasoning",
            submitted_by=self.detective_user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.sergeant_token.key}")

        response = self.client.post(
            f"/api/v1/investigation/reasonings/{reasoning.id}/approve/",
            {"decision": "approved", "justification": "Matches evidence graph"},
            format="json",
        )

        reasoning.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(reasoning.status, ReasoningSubmission.Status.APPROVED)
        self.assertTrue(ReasoningApproval.objects.filter(reasoning=reasoning).exists())

    def test_detective_cannot_approve_reasoning_even_with_approve_permission(self):
        RolePermission.objects.create(role=self.role_detective, permission=self.permission_approve)
        reasoning = ReasoningSubmission.objects.create(
            case_reference="CASE-1004",
            title="Detective submission",
            narrative="Pending detective reasoning",
            submitted_by=self.detective_user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.detective_token.key}")

        response = self.client.post(
            f"/api/v1/investigation/reasonings/{reasoning.id}/approve/",
            {"decision": "approved", "justification": "Should fail role policy"},
            format="json",
        )

        reasoning.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "WORKFLOW_POLICY_VIOLATION")
        self.assertEqual(reasoning.status, ReasoningSubmission.Status.PENDING)

    def test_sergeant_cannot_approve_reasoning_if_submitter_is_not_detective(self):
        reasoning = ReasoningSubmission.objects.create(
            case_reference="CASE-1005",
            title="Officer submission",
            narrative="Pending non-detective reasoning",
            submitted_by=self.officer_user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.sergeant_token.key}")

        response = self.client.post(
            f"/api/v1/investigation/reasonings/{reasoning.id}/approve/",
            {"decision": "approved", "justification": "Should fail workflow submitter policy"},
            format="json",
        )

        reasoning.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "WORKFLOW_POLICY_VIOLATION")
        self.assertEqual(reasoning.status, ReasoningSubmission.Status.PENDING)
