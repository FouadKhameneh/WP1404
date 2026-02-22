from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.cases.models import Case, CaseParticipant, Complaint, ComplaintReview


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


class ComplaintIntakeModelTests(TestCase):
    def setUp(self):
        self.cadet = get_user_model().objects.create_user(
            username="cadet10",
            email="cadet10@example.com",
            password="StrongPass123!",
            phone="09120030001",
            national_id="9300000001",
            full_name="Cadet Ten",
        )
        self.complainant = get_user_model().objects.create_user(
            username="complainant10",
            email="complainant10@example.com",
            password="StrongPass123!",
            phone="09120030002",
            national_id="9300000002",
            full_name="Complainant Ten",
        )
        self.case = Case.objects.create(
            title="Complaint intake case",
            summary="Cadet validation flow",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.COMPLAINT,
            created_by=self.cadet,
        )
        self.complaint = Complaint.objects.create(
            case=self.case,
            complainant=self.complainant,
            description="A detailed complaint for validation.",
        )

    def test_rejected_review_requires_rejection_reason(self):
        with self.assertRaises(ValidationError):
            ComplaintReview.objects.create(
                complaint=self.complaint,
                reviewer=self.cadet,
                decision=ComplaintReview.Decision.REJECTED,
                rejection_reason="",
            )

    def test_rejected_reviews_increment_counter_and_finalize_on_third_attempt(self):
        ComplaintReview.objects.create(
            complaint=self.complaint,
            reviewer=self.cadet,
            decision=ComplaintReview.Decision.REJECTED,
            rejection_reason="Missing key details.",
        )
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, Complaint.Status.REJECTED)
        self.assertEqual(self.complaint.validation_counter.invalid_attempt_count, 1)
        self.assertEqual(self.complaint.rejection_reason, "Missing key details.")

        ComplaintReview.objects.create(
            complaint=self.complaint,
            reviewer=self.cadet,
            decision=ComplaintReview.Decision.REJECTED,
            rejection_reason="Insufficient supporting info.",
        )
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, Complaint.Status.REJECTED)
        self.assertEqual(self.complaint.validation_counter.invalid_attempt_count, 2)

        ComplaintReview.objects.create(
            complaint=self.complaint,
            reviewer=self.cadet,
            decision=ComplaintReview.Decision.REJECTED,
            rejection_reason="Third rejection.",
        )
        self.complaint.refresh_from_db()
        self.case.refresh_from_db()
        self.assertEqual(self.complaint.status, Complaint.Status.FINAL_INVALID)
        self.assertIsNotNone(self.complaint.invalidated_at)
        self.assertEqual(self.complaint.validation_counter.invalid_attempt_count, 3)
        self.assertEqual(self.case.status, Case.Status.FINAL_INVALID)

    def test_complaint_cannot_be_reviewed_after_terminal_invalidation(self):
        for reason in ["First rejection", "Second rejection", "Third rejection"]:
            ComplaintReview.objects.create(
                complaint=self.complaint,
                reviewer=self.cadet,
                decision=ComplaintReview.Decision.REJECTED,
                rejection_reason=reason,
            )

        with self.assertRaises(ValidationError):
            ComplaintReview.objects.create(
                complaint=self.complaint,
                reviewer=self.cadet,
                decision=ComplaintReview.Decision.APPROVED,
            )

    def test_approved_review_sets_validated_state(self):
        ComplaintReview.objects.create(
            complaint=self.complaint,
            reviewer=self.cadet,
            decision=ComplaintReview.Decision.APPROVED,
        )
        self.complaint.refresh_from_db()

        self.assertEqual(self.complaint.status, Complaint.Status.VALIDATED)
        self.assertIsNotNone(self.complaint.validated_at)
        self.assertIsNotNone(self.complaint.reviewed_at)
        self.assertEqual(self.complaint.rejection_reason, "")


class ComplaintIntakeApiTests(APITestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin_cases01",
            email="admin_cases01@example.com",
            password="StrongPass123!",
            phone="09120040001",
            national_id="9400000001",
            full_name="Admin Cases One",
        )
        self.cadet_user = get_user_model().objects.create_user(
            username="cadet_api01",
            email="cadet_api01@example.com",
            password="StrongPass123!",
            phone="09120040002",
            national_id="9400000002",
            full_name="Cadet Api One",
        )
        self.complainant_user = get_user_model().objects.create_user(
            username="complainant_api01",
            email="complainant_api01@example.com",
            password="StrongPass123!",
            phone="09120040003",
            national_id="9400000003",
            full_name="Complainant Api One",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other_api01",
            email="other_api01@example.com",
            password="StrongPass123!",
            phone="09120040004",
            national_id="9400000004",
            full_name="Other Api One",
        )

        self.permission_submit = Permission.objects.create(
            code="cases.complaints.submit",
            name="Submit Complaint",
            resource="cases.complaints",
            action="submit",
        )
        self.permission_review = Permission.objects.create(
            code="cases.complaints.review",
            name="Review Complaint",
            resource="cases.complaints",
            action="review",
        )
        self.permission_resubmit = Permission.objects.create(
            code="cases.complaints.resubmit",
            name="Resubmit Complaint",
            resource="cases.complaints",
            action="resubmit",
        )

        self.role_cadet = Role.objects.create(key="cadet", name="Cadet")
        self.role_base_user = Role.objects.create(key="base_user", name="Base User")

        RolePermission.objects.create(role=self.role_cadet, permission=self.permission_review)
        RolePermission.objects.create(role=self.role_base_user, permission=self.permission_submit)
        RolePermission.objects.create(role=self.role_base_user, permission=self.permission_resubmit)

        UserRoleAssignment.objects.create(user=self.cadet_user, role=self.role_cadet, assigned_by=self.admin_user)
        UserRoleAssignment.objects.create(
            user=self.complainant_user,
            role=self.role_base_user,
            assigned_by=self.admin_user,
        )
        UserRoleAssignment.objects.create(user=self.other_user, role=self.role_base_user, assigned_by=self.admin_user)

        self.cadet_token = Token.objects.create(user=self.cadet_user)
        self.complainant_token = Token.objects.create(user=self.complainant_user)
        self.other_token = Token.objects.create(user=self.other_user)

        self.submit_url = "/api/v1/cases/complaints/"

    def test_submit_complaint_creates_submitted_record(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.complainant_token.key}")
        payload = {"description": "Citizen complaint about suspicious activity."}

        response = self.client.post(self.submit_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], Complaint.Status.SUBMITTED)
        self.assertIsNone(response.data["data"]["case"])

    def test_cadet_approval_creates_case_for_valid_complaint(self):
        complaint = Complaint.objects.create(
            complainant=self.complainant_user,
            description="Complaint that should become a case.",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.cadet_token.key}")

        response = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/review/",
            {"decision": ComplaintReview.Decision.APPROVED},
            format="json",
        )

        complaint.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["complaint"]["status"], Complaint.Status.VALIDATED)
        self.assertIsNotNone(complaint.case_id)
        self.assertEqual(complaint.case.source_type, Case.SourceType.COMPLAINT)
        self.assertEqual(complaint.case.assigned_role_key, "police_officer")

    def test_reject_resubmit_and_terminal_invalidation_flow(self):
        complaint = Complaint.objects.create(
            complainant=self.complainant_user,
            description="Complaint requiring multiple revisions.",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.cadet_token.key}")
        first_reject = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/review/",
            {"decision": ComplaintReview.Decision.REJECTED, "rejection_reason": "Missing evidence."},
            format="json",
        )
        self.assertEqual(first_reject.status_code, status.HTTP_200_OK)
        self.assertEqual(first_reject.data["data"]["complaint"]["status"], Complaint.Status.REJECTED)
        self.assertEqual(first_reject.data["data"]["complaint"]["invalid_attempt_count"], 1)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.complainant_token.key}")
        first_resubmit = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/resubmit/",
            {"description": "Updated complaint details after first rejection."},
            format="json",
        )
        self.assertEqual(first_resubmit.status_code, status.HTTP_200_OK)
        self.assertEqual(first_resubmit.data["data"]["status"], Complaint.Status.SUBMITTED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.cadet_token.key}")
        second_reject = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/review/",
            {"decision": ComplaintReview.Decision.REJECTED, "rejection_reason": "Still incomplete."},
            format="json",
        )
        self.assertEqual(second_reject.status_code, status.HTTP_200_OK)
        self.assertEqual(second_reject.data["data"]["complaint"]["status"], Complaint.Status.REJECTED)
        self.assertEqual(second_reject.data["data"]["complaint"]["invalid_attempt_count"], 2)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.complainant_token.key}")
        second_resubmit = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/resubmit/",
            {"description": "Updated complaint details after second rejection."},
            format="json",
        )
        self.assertEqual(second_resubmit.status_code, status.HTTP_200_OK)
        self.assertEqual(second_resubmit.data["data"]["status"], Complaint.Status.SUBMITTED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.cadet_token.key}")
        third_reject = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/review/",
            {"decision": ComplaintReview.Decision.REJECTED, "rejection_reason": "Third failed validation."},
            format="json",
        )
        self.assertEqual(third_reject.status_code, status.HTTP_200_OK)
        self.assertEqual(third_reject.data["data"]["complaint"]["status"], Complaint.Status.FINAL_INVALID)
        self.assertEqual(third_reject.data["data"]["complaint"]["invalid_attempt_count"], 3)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.complainant_token.key}")
        terminal_resubmit = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/resubmit/",
            {"description": "Should fail after third rejection."},
            format="json",
        )
        self.assertEqual(terminal_resubmit.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(terminal_resubmit.data["success"])
        self.assertEqual(terminal_resubmit.data["error"]["code"], "WORKFLOW_POLICY_VIOLATION")

    def test_non_owner_cannot_resubmit_complaint(self):
        complaint = Complaint.objects.create(
            complainant=self.complainant_user,
            description="Complaint owned by another user.",
            status=Complaint.Status.REJECTED,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.other_token.key}")

        response = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/resubmit/",
            {"description": "Unauthorized resubmission attempt."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "FORBIDDEN")

    def test_non_cadet_cannot_review_even_with_review_permission(self):
        RolePermission.objects.create(role=self.role_base_user, permission=self.permission_review)
        complaint = Complaint.objects.create(
            complainant=self.complainant_user,
            description="Complaint should require cadet role for review.",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.complainant_token.key}")

        response = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/review/",
            {"decision": ComplaintReview.Decision.APPROVED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "ROLE_POLICY_VIOLATION")
