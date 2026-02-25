from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.cases.models import Case, CaseParticipant
from apps.wanted.models import Wanted
from apps.wanted.services import promote_to_most_wanted


class WantedLifecycleTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin_w", email="admin_w@example.com", password="StrongPass123!",
            phone="09120007001", national_id="7000000001", full_name="Admin W",
        )
        self.user = get_user_model().objects.create_user(
            username="user_w", email="user_w@example.com", password="StrongPass123!",
            phone="09120007002", national_id="7000000002", full_name="User W",
        )
        Token.objects.create(user=self.user)
        perm, _ = Permission.objects.get_or_create(
            code="wanted.view",
            defaults={"name": "View wanted", "resource": "wanted", "action": "view"},
        )
        role, _ = Role.objects.get_or_create(key="officer", defaults={"name": "Officer"})
        RolePermission.objects.get_or_create(role=role, permission=perm)
        UserRoleAssignment.objects.create(user=self.user, role=role, assigned_by=self.admin)

        self.case = Case.objects.create(
            title="Wanted case",
            summary="Summary",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.COMPLAINT,
            status=Case.Status.SUSPECT_ASSESSMENT,
            created_by=self.admin,
        )

    def test_on_suspect_mark_wanted_created(self):
        """Adding a suspect to a case creates a Wanted entry (signal)."""
        participant = CaseParticipant.objects.create(
            case=self.case,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
            role_in_case=CaseParticipant.RoleInCase.SUSPECT,
            full_name="Suspect W",
            national_id="7000001001",
            added_by=self.admin,
        )
        self.assertTrue(Wanted.objects.filter(case=self.case, participant=participant).exists())
        w = Wanted.objects.get(case=self.case, participant=participant)
        self.assertEqual(w.status, Wanted.Status.WANTED)

    def test_list_wanted_and_most_wanted_filter(self):
        CaseParticipant.objects.create(
            case=self.case,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
            role_in_case=CaseParticipant.RoleInCase.SUSPECT,
            full_name="S",
            national_id="7000001002",
            added_by=self.admin,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get(user=self.user).key}")
        r = self.client.get("/api/v1/wanted/", format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(r.data["data"]["results"]), 1)
        r2 = self.client.get("/api/v1/wanted/?status=most_wanted", format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

    def test_promote_to_most_wanted_after_one_month(self):
        from datetime import timedelta
        participant = CaseParticipant.objects.create(
            case=self.case,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
            role_in_case=CaseParticipant.RoleInCase.SUSPECT,
            full_name="Old Suspect",
            national_id="7000001003",
            added_by=self.admin,
        )
        w = Wanted.objects.get(case=self.case, participant=participant)
        w.marked_at = timezone.now() - timedelta(days=31)
        w.save(update_fields=["marked_at"])
        count = promote_to_most_wanted()
        self.assertGreaterEqual(count, 1)
        w.refresh_from_db()
        self.assertEqual(w.status, Wanted.Status.MOST_WANTED)
        self.assertIsNotNone(w.promoted_at)
