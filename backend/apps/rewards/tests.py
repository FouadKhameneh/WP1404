from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.cases.models import Case, CaseParticipant
from apps.rewards.models import RewardComputationSnapshot
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
        self.wanted = Wanted.objects.create(
            case=self.case_level2,
            participant=self.participant,
            status=Wanted.Status.MOST_WANTED,
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
