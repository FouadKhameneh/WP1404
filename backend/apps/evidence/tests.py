from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.cases.models import Case
from apps.evidence.models import Evidence


class EvidenceModelInvariantTests(TestCase):
    """Model invariant tests for Evidence."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ev_user",
            email="ev@example.com",
            password="StrongPass123!",
            phone="09120009999",
            national_id="1200000099",
            full_name="Evidence User",
        )
        self.case = Case.objects.create(
            title="Case for evidence",
            summary="",
            level=Case.Level.LEVEL_1,
            source_type=Case.SourceType.SCENE_REPORT,
            status=Case.Status.SUBMITTED,
            created_by=self.user,
        )

    def test_evidence_model_invariant_required_fields(self):
        e = Evidence.objects.create(
            title="Test evidence",
            description="",
            evidence_type=Evidence.EvidenceType.OTHER,
            registered_at=timezone.now(),
            case=self.case,
            registrar=self.user,
        )
        self.assertEqual(e.evidence_type, Evidence.EvidenceType.OTHER)
        self.assertEqual(e.case_id, self.case.id)
        self.assertEqual(e.title, "Test evidence")

    def test_evidence_requires_case(self):
        with self.assertRaises(Exception):
            Evidence.objects.create(
                title="Orphan",
                description="",
                evidence_type=Evidence.EvidenceType.OTHER,
                registered_at=timezone.now(),
                case=None,
                registrar=self.user,
            )