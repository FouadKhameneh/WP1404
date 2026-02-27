from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.cases.models import Case, CaseParticipant
from apps.rewards.models import RewardComputationSnapshot, RewardTip
from apps.rewards.services import (
    REWARD_MULTIPLIER_RIALS,
    compute_and_persist_snapshots,
    compute_ranking_and_reward_for_person,
    days_under_surveillance,
    level_to_di,
)
from apps.wanted.models import Wanted


class RankingRewardFormulaTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin_r",
            email="admin_r@example.com",
            password="StrongPass123!",
            phone="09120008001",
            national_id="8000000001",
            full_name="Admin R",
        )
        self.case_level2 = Case.objects.create(
            title="Case L2",
            summary="",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.COMPLAINT,
            status=Case.Status.SUSPECT_ASSESSMENT,
            created_by=self.admin,
        )
        self.participant = CaseParticipant.objects.create(
            case=self.case_level2,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
            role_in_case=CaseParticipant.RoleInCase.SUSPECT,
            full_name="Suspect R",
            national_id="8000001001",
            added_by=self.admin,
        )
        self.wanted, _ = Wanted.objects.get_or_create(
            case=self.case_level2,
            participant=self.participant,
            defaults={"status": Wanted.Status.MOST_WANTED},
        )

    def test_level_to_di(self):
        self.assertEqual(level_to_di(Case.Level.LEVEL_3), 1)
        self.assertEqual(level_to_di(Case.Level.LEVEL_2), 2)
        self.assertEqual(level_to_di(Case.Level.LEVEL_1), 3)
        self.assertEqual(level_to_di(Case.Level.CRITICAL), 4)

    def test_ranking_and_reward_formula(self):
        data = compute_ranking_and_reward_for_person([self.wanted])
        self.assertIsNotNone(data)
        self.assertEqual(data["max_crime_level_di"], 2)
        self.assertEqual(data["ranking_score"], data["max_days_lj"] * data["max_crime_level_di"])
        self.assertEqual(data["reward_amount_rials"], data["ranking_score"] * REWARD_MULTIPLIER_RIALS)

    def test_compute_and_persist_snapshots(self):
        created = compute_and_persist_snapshots()
        self.assertGreaterEqual(len(created), 1)
        snap = RewardComputationSnapshot.objects.filter(national_id="8000001001").first()
        self.assertIsNotNone(snap)
        self.assertEqual(snap.ranking_score, snap.max_days_lj * snap.max_crime_level_di)
        self.assertEqual(snap.reward_amount_rials, snap.ranking_score * REWARD_MULTIPLIER_RIALS)


class RewardTipWorkflowTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin_t", email="admin_t@example.com", password="StrongPass123!",
            phone="09120009001", national_id="9000000001", full_name="Admin T",
        )
        self.base_user = get_user_model().objects.create_user(
            username="base_t", email="base_t@example.com", password="StrongPass123!",
            phone="09120009002", national_id="9000000002", full_name="Base T",
        )
        self.officer_user = get_user_model().objects.create_user(
            username="off_t", email="off_t@example.com", password="StrongPass123!",
            phone="09120009003", national_id="9000000003", full_name="Officer T",
        )
        self.detective_user = get_user_model().objects.create_user(
            username="det_t", email="det_t@example.com", password="StrongPass123!",
            phone="09120009004", national_id="9000000004", full_name="Detective T",
        )
        from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
        from rest_framework.authtoken.models import Token
        for code, name, resource, action in [
            ("rewards.tip.view", "View", "rewards.tip", "view"),
            ("rewards.tip.submit", "Submit", "rewards.tip", "submit"),
            ("rewards.tip.review", "Review", "rewards.tip", "review"),
        ]:
            perm, _ = Permission.objects.get_or_create(code=code, defaults={"name": name, "resource": resource, "action": action})
            for key in ["base_user", "officer", "detective"]:
                role, _ = Role.objects.get_or_create(key=key, defaults={"name": key})
                RolePermission.objects.get_or_create(role=role, permission=perm)
        UserRoleAssignment.objects.create(user=self.base_user, role=Role.objects.get(key="base_user"), assigned_by=self.admin)
        UserRoleAssignment.objects.create(user=self.officer_user, role=Role.objects.get(key="officer"), assigned_by=self.admin)
        UserRoleAssignment.objects.create(user=self.detective_user, role=Role.objects.get(key="detective"), assigned_by=self.admin)
        self.base_token = Token.objects.create(user=self.base_user)
        self.officer_token = Token.objects.create(user=self.officer_user)
        self.detective_token = Token.objects.create(user=self.detective_user)

    def test_tip_workflow_approval_generates_claim_id(self):
        from rest_framework import status
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.base_token.key}")
        r = self.client.post(
            "/api/v1/rewards/tips/",
            {"case_reference": "CASE-X", "subject": "Tip", "content": "Info here."},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        tip_id = r.data["data"]["id"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.officer_token.key}")
        self.client.post(f"/api/v1/rewards/tips/{tip_id}/review/", {"approved": True}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.detective_token.key}")
        r3 = self.client.post(f"/api/v1/rewards/tips/{tip_id}/review/", {"approved": True}, format="json")
        self.assertEqual(r3.status_code, status.HTTP_200_OK)
        self.assertEqual(r3.data["data"]["status"], "approved")
        self.assertTrue(r3.data["data"]["reward_claim_id"].startswith("RWD-"))
        self.assertEqual(len(r3.data["data"]["reward_claim_id"]), 16)  # RWD- + 12 hex


class RewardClaimVerifyTests(APITestCase):
    """Task 39: Verify claim using National ID + Unique ID; authorized police ranks only."""

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin_v", email="admin_v@example.com", password="StrongPass123!",
            phone="09120010001", national_id="1000000001", full_name="Admin V",
        )
        self.submitter = get_user_model().objects.create_user(
            username="sub_v", email="sub_v@example.com", password="StrongPass123!",
            phone="09120010002", national_id="1000000002", full_name="Submitter V",
        )
        self.officer_user = get_user_model().objects.create_user(
            username="off_v", email="off_v@example.com", password="StrongPass123!",
            phone="09120010003", national_id="1000000003", full_name="Officer V",
        )
        from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
        from rest_framework.authtoken.models import Token
        perm, _ = Permission.objects.get_or_create(
            code="rewards.claim.verify",
            defaults={"name": "Verify claim", "resource": "rewards.claim", "action": "verify"},
        )
        role, _ = Role.objects.get_or_create(key="officer", defaults={"name": "Officer"})
        RolePermission.objects.get_or_create(role=role, permission=perm)
        UserRoleAssignment.objects.create(user=self.officer_user, role=role, assigned_by=self.admin)
        self.officer_token = Token.objects.create(user=self.officer_user)
        self.tip = RewardTip.objects.create(
            submitted_by=self.submitter,
            case_reference="CASE-V",
            subject="Tip",
            content="Content",
            status=RewardTip.Status.APPROVED,
            reward_claim_id="RWD-ABC123DEF456",
        )

    def test_verify_claim_success(self):
        from rest_framework import status
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.officer_token.key}")
        r = self.client.post(
            "/api/v1/rewards/verify-claim/",
            {"national_id": "1000000002", "reward_claim_id": "RWD-ABC123DEF456"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(r.data["data"]["valid"])
        self.assertEqual(r.data["data"]["reward_claim_id"], "RWD-ABC123DEF456")

    def test_verify_claim_wrong_national_id_invalid(self):
        from rest_framework import status
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.officer_token.key}")
        r = self.client.post(
            "/api/v1/rewards/verify-claim/",
            {"national_id": "9999999999", "reward_claim_id": "RWD-ABC123DEF456"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertFalse(r.data["data"]["valid"])
