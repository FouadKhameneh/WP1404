from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.cases.models import Case


class CaseModelTests(TestCase):
    def setUp(self):
        self.creator = get_user_model().objects.create_user(
            username="officer10",
            email="officer10@example.com",
            password="StrongPass123!",
            phone="09120010001",
            national_id="9100000001",
            full_name="Officer Ten",
        )
        self.assignee = get_user_model().objects.create_user(
            username="detective10",
            email="detective10@example.com",
            password="StrongPass123!",
            phone="09120010002",
            national_id="9100000002",
            full_name="Detective Ten",
        )

    def test_case_defaults_map_priority_from_level(self):
        case = Case.objects.create(
            title="Organized crime case",
            summary="Critical investigation",
            level=Case.Level.CRITICAL,
            source_type=Case.SourceType.SCENE_REPORT,
            created_by=self.creator,
        )

        self.assertTrue(case.case_number.startswith("CASE-"))
        self.assertEqual(case.priority, Case.Priority.URGENT)
        self.assertEqual(case.status, Case.Status.SUBMITTED)
        self.assertIsNotNone(case.submitted_at)

    def test_case_status_transitions_set_lifecycle_timestamps(self):
        case = Case.objects.create(
            title="Complaint case",
            summary="Initial complaint intake",
            level=Case.Level.LEVEL_3,
            source_type=Case.SourceType.COMPLAINT,
            created_by=self.creator,
        )

        self.assertIsNotNone(case.submitted_at)

        case.status = Case.Status.UNDER_REVIEW
        case.save()
        self.assertIsNotNone(case.under_review_at)

        case.status = Case.Status.ACTIVE_INVESTIGATION
        case.save()
        self.assertIsNotNone(case.investigation_started_at)

        case.status = Case.Status.CLOSED
        case.save()
        self.assertIsNotNone(case.closed_at)

    def test_assignment_metadata_sets_assigned_at(self):
        case = Case.objects.create(
            title="Assignment case",
            summary="Assign detective",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.SCENE_REPORT,
            created_by=self.creator,
        )

        case.assigned_to = self.assignee
        case.assigned_by = self.creator
        case.assigned_role_key = "detective"
        case.assignment_notes = "Primary detective assignment"
        case.save()

        self.assertEqual(case.assigned_to_id, self.assignee.id)
        self.assertEqual(case.assigned_by_id, self.creator.id)
        self.assertEqual(case.assigned_role_key, "detective")
        self.assertEqual(case.assignment_notes, "Primary detective assignment")
        self.assertIsNotNone(case.assigned_at)

    def test_unassigning_case_clears_assigned_at(self):
        case = Case.objects.create(
            title="Unassignment case",
            summary="Temporary assignment",
            level=Case.Level.LEVEL_1,
            source_type=Case.SourceType.SCENE_REPORT,
            created_by=self.creator,
            assigned_to=self.assignee,
            assigned_by=self.creator,
            assigned_role_key="detective",
        )

        self.assertIsNotNone(case.assigned_at)
        case.assigned_to = None
        case.assigned_by = None
        case.assigned_role_key = ""
        case.save()
        self.assertIsNone(case.assigned_at)
