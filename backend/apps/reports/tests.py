from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.cases.models import Case


class ReportsAPITests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin_r", email="admin_r@example.com", password="StrongPass123!",
            phone="09120012001", national_id="1200000001", full_name="Admin R",
        )
        self.user = get_user_model().objects.create_user(
            username="user_r", email="user_r@example.com", password="StrongPass123!",
            phone="09120012002", national_id="1200000002", full_name="User R",
        )
        Token.objects.create(user=self.user)
        perm, _ = Permission.objects.get_or_create(
            code="reports.view",
            defaults={"name": "View reports", "resource": "reports", "action": "view"},
        )
        role, _ = Role.objects.get_or_create(key="captain", defaults={"name": "Captain"})
        RolePermission.objects.get_or_create(role=role, permission=perm)
        UserRoleAssignment.objects.create(user=self.user, role=role, assigned_by=self.admin)

        Case.objects.create(
            title="C1",
            summary="",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.COMPLAINT,
            status=Case.Status.SUBMITTED,
            created_by=self.admin,
        )

    def test_homepage_stats_returns_aggregates(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get(user=self.user).key}")
        r = self.client.get("/api/v1/reports/homepage/", format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("total_cases", r.data["data"])
        self.assertIn("active_cases", r.data["data"])
        self.assertGreaterEqual(r.data["data"]["total_cases"], 1)

    def test_general_report_returns_all_sections(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get(user=self.user).key}")
        r = self.client.get("/api/v1/reports/general/", format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("homepage", r.data["data"])
        self.assertIn("case_counts", r.data["data"])
        self.assertIn("approvals", r.data["data"])
        self.assertIn("wanted_rankings", r.data["data"])
        self.assertIn("reward_outcomes", r.data["data"])
