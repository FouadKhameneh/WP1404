from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.cases.models import Case, CaseParticipant
from apps.payments.models import PaymentTransaction


class PaymentModuleTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin_p",
            email="admin_p@example.com",
            password="StrongPass123!",
            phone="09120011001",
            national_id="1100000001",
            full_name="Admin P",
        )
        self.user = get_user_model().objects.create_user(
            username="user_p",
            email="user_p@example.com",
            password="StrongPass123!",
            phone="09120011002",
            national_id="1100000002",
            full_name="User P",
        )
        Token.objects.create(user=self.user)
        perm, _ = Permission.objects.get_or_create(
            code="payments.initiate",
            defaults={"name": "Initiate payment", "resource": "payments", "action": "initiate"},
        )
        role, _ = Role.objects.get_or_create(key="sergeant", defaults={"name": "Sergeant"})
        RolePermission.objects.get_or_create(role=role, permission=perm)
        UserRoleAssignment.objects.create(user=self.user, role=role, assigned_by=self.admin)

        self.case = Case.objects.create(
            title="Case L2",
            summary="",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.COMPLAINT,
            status=Case.Status.SUSPECT_ASSESSMENT,
            created_by=self.admin,
        )
        self.participant = CaseParticipant.objects.create(
            case=self.case,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
            role_in_case=CaseParticipant.RoleInCase.SUSPECT,
            full_name="Suspect P",
            national_id="1100001001",
            added_by=self.admin,
        )

    def test_initiate_creates_transaction_and_returns_redirect(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get(user=self.user).key}")
        r = self.client.post(
            "/api/v1/payments/initiate/",
            {"case": self.case.id, "participant": self.participant.id, "amount_rials": 10_000_000},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIn("redirect_url", r.data["data"])
        self.assertIn("transaction_id", r.data["data"])
        self.assertTrue(PaymentTransaction.objects.filter(case=self.case).exists())

    def test_callback_verifies_and_updates_transaction(self):
        txn = PaymentTransaction.objects.create(
            case=self.case,
            participant=self.participant,
            amount_rials=5_000_000,
            gateway_name="mock",
            gateway_ref="MOCK-1",
            status=PaymentTransaction.Status.PENDING,
        )
        r = self.client.get(
            f"/api/v1/payments/callback/",
            {"transaction_id": txn.id, "ref": "MOCK-1", "status": "ok"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        txn.refresh_from_db()
        self.assertEqual(txn.status, PaymentTransaction.Status.SUCCESS)
        self.assertIsNotNone(txn.verified_at)
