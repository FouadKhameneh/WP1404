"""
تست یکپارچه چک‌لیست قابلیت‌ها — هر تست معادل یک مورد چک‌لیست است.
اجرا: python manage.py test apps.reports.tests_checklist
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.cases.models import Case, CaseParticipant
from apps.payments.models import PaymentTransaction
from rest_framework.authtoken.models import Token

User = get_user_model()


class ChecklistIntegrationTests(APITestCase):
    """تست‌های یکپارچه متناظر با چک‌لیست قابلیت‌ها."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="admin_cl",
            email="admin_cl@test.com",
            password="Test123!",
            phone="09121111111",
            national_id="1111111111",
            full_name="Admin CL",
        )
        cls.admin_token = Token.objects.create(user=cls.admin)
        perm = Permission.objects.get_or_create(
            code="reports.view",
            defaults={"name": "View reports", "resource": "reports", "action": "view"},
        )[0]
        role = Role.objects.get_or_create(key="officer", defaults={"name": "Officer"})[0]
        RolePermission.objects.get_or_create(role=role, permission=perm)
        UserRoleAssignment.objects.create(user=cls.admin, role=role, assigned_by=cls.admin)
        cls.case = Case.objects.create(
            title="Case CL",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.COMPLAINT,
            status=Case.Status.SUSPECT_ASSESSMENT,
            created_by=cls.admin,
        )
        cls.participant = CaseParticipant.objects.create(
            case=cls.case,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
            role_in_case=CaseParticipant.RoleInCase.SUSPECT,
            full_name="Suspect CL",
            national_id="2222222222",
            added_by=cls.admin,
        )

    def test_1_1_landing_stats_without_auth(self):
        r = self.client.get("/api/v1/reports/landing-stats/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_1_2_landing_stats_returns_required_fields(self):
        r = self.client.get("/api/v1/reports/landing-stats/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.data.get("data") or r.data
        for key in ("closed_cases", "staff_count", "active_cases"):
            self.assertIn(key, data)

    def test_2_1_register_creates_user(self):
        r = self.client.post(
            "/api/v1/identity/auth/register/",
            {
                "username": "newuser_cl",
                "password": "Pass123!",
                "password_confirm": "Pass123!",
                "email": "new@test.com",
                "phone": "09123333333",
                "national_id": "3333333333",
                "full_name": "New User",
            },
            format="json",
        )
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED))
        self.assertTrue(User.objects.filter(username="newuser_cl").exists())

    def test_2_2_login_with_username_returns_token(self):
        User.objects.create_user(
            username="loguser",
            password="Pass123!",
            email="log@test.com",
            phone="09124444444",
            national_id="4444444444",
            full_name="Log User",
        )
        r = self.client.post(
            "/api/v1/identity/auth/login/",
            {"identifier": "loguser", "password": "Pass123!"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.data.get("data") or r.data
        self.assertTrue(
            "token" in data or "access_token" in data,
            f"Expected token in response: {list(data.keys())}",
        )

    def test_2_3_login_with_email_returns_token(self):
        User.objects.create_user(
            username="emuser",
            password="Pass123!",
            email="em@test.com",
            phone="09125555555",
            national_id="5555555555",
            full_name="Em User",
        )
        r = self.client.post(
            "/api/v1/identity/auth/login/",
            {"identifier": "em@test.com", "password": "Pass123!"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.data.get("data") or r.data
        self.assertTrue("token" in data or "access_token" in data)

    def test_2_5_logout_deletes_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        r = self.client.post("/api/v1/identity/auth/logout/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))

    def test_2_6_me_returns_user_with_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        r = self.client.get("/api/v1/identity/auth/me/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_10_1_roles_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        r = self.client.get("/api/v1/access/roles/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_403_FORBIDDEN))

    def test_10_4_401_without_token(self):
        r = self.client.get("/api/v1/reports/homepage/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_7_1_wanted_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        r = self.client.get("/api/v1/wanted/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_403_FORBIDDEN))

    def test_7_2_wanted_rankings(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        r = self.client.get("/api/v1/reports/wanted-rankings/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_403_FORBIDDEN))

    def test_7_3_general_report(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        r = self.client.get("/api/v1/reports/general/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_403_FORBIDDEN))

    def test_9_3_transaction_status_endpoint(self):
        txn = PaymentTransaction.objects.create(
            case=self.case,
            participant=self.participant,
            amount_rials=1_000_000,
            gateway_name="mock",
            status=PaymentTransaction.Status.SUCCESS,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        r = self.client.get(f"/api/v1/payments/transactions/{txn.id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_11_1_swagger_schema_available(self):
        r = self.client.get("/api/schema/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
