from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.cases.models import Case, CaseParticipant
from apps.judiciary.models import CaseVerdict


class JudiciaryReferralPackageTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin_j", email="admin_j@example.com", password="StrongPass123!",
            phone="09120006001", national_id="6000000001", full_name="Admin J",
        )
        self.judge_user = get_user_model().objects.create_user(
            username="judge_j", email="judge_j@example.com", password="StrongPass123!",
            phone="09120006002", national_id="6000000002", full_name="Judge J",
        )
        Token.objects.create(user=self.judge_user)
        perm, _ = Permission.objects.get_or_create(
            code="judiciary.referral.view",
            defaults={"name": "View referral", "resource": "judiciary.referral", "action": "view"},
        )
        role, _ = Role.objects.get_or_create(key="judge", defaults={"name": "Judge"})
        RolePermission.objects.get_or_create(role=role, permission=perm)
        UserRoleAssignment.objects.create(user=self.judge_user, role=role, assigned_by=self.admin)

        self.case = Case.objects.create(
            title="Ref case",
            summary="Summary",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.COMPLAINT,
            status=Case.Status.REFERRAL_READY,
            created_by=self.admin,
        )

    def test_referral_package_returns_case_participants_evidence(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get(user=self.judge_user).key}")
        response = self.client.get(f"/api/v1/judiciary/referral-package/{self.case.id}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["case"]["case_number"], self.case.case_number)
        self.assertIn("participants", data)
        self.assertIn("evidence", data)


class JudiciaryVerdictTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin_v", email="admin_v@example.com", password="StrongPass123!",
            phone="09120006003", national_id="6000000003", full_name="Admin V",
        )
        self.judge_user = get_user_model().objects.create_user(
            username="judge_v", email="judge_v@example.com", password="StrongPass123!",
            phone="09120006004", national_id="6000000004", full_name="Judge V",
        )
        Token.objects.create(user=self.judge_user)
        for code, name, resource, action in [
            ("judiciary.verdict.view", "View verdict", "judiciary.verdict", "view"),
            ("judiciary.verdict.add", "Add verdict", "judiciary.verdict", "add"),
        ]:
            perm, _ = Permission.objects.get_or_create(code=code, defaults={"name": name, "resource": resource, "action": action})
            role, _ = Role.objects.get_or_create(key="judge", defaults={"name": "Judge"})
            RolePermission.objects.get_or_create(role=role, permission=perm)
        UserRoleAssignment.objects.create(user=self.judge_user, role=Role.objects.get(key="judge"), assigned_by=self.admin)

        self.case = Case.objects.create(
            title="Trial case",
            summary="Summary",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.COMPLAINT,
            status=Case.Status.IN_TRIAL,
            created_by=self.admin,
        )

    def test_judge_can_record_verdict_and_case_closes(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get(user=self.judge_user).key}")
        response = self.client.post(
            f"/api/v1/judiciary/cases/{self.case.id}/verdict/",
            {"verdict": "guilty", "punishment_title": "6 months", "punishment_description": "Prison term."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["verdict"], "guilty")
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, Case.Status.CLOSED)
        self.assertIsNotNone(self.case.closed_at)
        self.assertTrue(CaseVerdict.objects.filter(case=self.case).exists())
