from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.cases.models import Case, CaseParticipant


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


class CaseParticipantModelTests(TestCase):
    def setUp(self):
        self.creator = get_user_model().objects.create_user(
            username="sergeant10",
            email="sergeant10@example.com",
            password="StrongPass123!",
            phone="09120020001",
            national_id="9200000001",
            full_name="Sergeant Ten",
        )
        self.judge_user = get_user_model().objects.create_user(
            username="judge10",
            email="judge10@example.com",
            password="StrongPass123!",
            phone="09120020002",
            national_id="9200000002",
            full_name="Judge Ten",
        )
        self.case = Case.objects.create(
            title="Participant case",
            summary="Participant tracking",
            level=Case.Level.LEVEL_1,
            source_type=Case.SourceType.COMPLAINT,
            created_by=self.creator,
        )

    def test_personnel_participant_links_to_user(self):
        participant = CaseParticipant.objects.create(
            case=self.case,
            participant_kind=CaseParticipant.ParticipantKind.PERSONNEL,
            role_in_case=CaseParticipant.RoleInCase.JUDGE,
            user=self.judge_user,
            added_by=self.creator,
        )

        self.assertEqual(participant.user_id, self.judge_user.id)
        self.assertEqual(participant.role_in_case, CaseParticipant.RoleInCase.JUDGE)
        self.assertEqual(participant.participant_kind, CaseParticipant.ParticipantKind.PERSONNEL)

    def test_participant_requires_user_or_full_name(self):
        with self.assertRaises(IntegrityError):
            CaseParticipant.objects.create(
                case=self.case,
                participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
                role_in_case=CaseParticipant.RoleInCase.WITNESS,
                national_id="9400000001",
            )

    def test_unique_case_role_user_constraint(self):
        CaseParticipant.objects.create(
            case=self.case,
            participant_kind=CaseParticipant.ParticipantKind.PERSONNEL,
            role_in_case=CaseParticipant.RoleInCase.DETECTIVE,
            user=self.creator,
        )

        with self.assertRaises(IntegrityError):
            CaseParticipant.objects.create(
                case=self.case,
                participant_kind=CaseParticipant.ParticipantKind.PERSONNEL,
                role_in_case=CaseParticipant.RoleInCase.DETECTIVE,
                user=self.creator,
            )

    def test_unique_case_role_national_id_constraint_for_external_participant(self):
        CaseParticipant.objects.create(
            case=self.case,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
            role_in_case=CaseParticipant.RoleInCase.WITNESS,
            full_name="Witness One",
            national_id="9500000001",
        )

        with self.assertRaises(IntegrityError):
            CaseParticipant.objects.create(
                case=self.case,
                participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
                role_in_case=CaseParticipant.RoleInCase.WITNESS,
                full_name="Witness Duplicate",
                national_id="9500000001",
            )
