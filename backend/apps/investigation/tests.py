
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.cases.models import Case, CaseParticipant
from apps.investigation.models import (
    ReasoningApproval,
    ReasoningSubmission,
    SuspectAssessment,
    SuspectAssessmentScoreEntry,
)


class InvestigationAuthorizationPolicyTests(APITestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin02",
            email="admin02@example.com",
            password="StrongPass123!",
            phone="09120002001",
            national_id="2000000001",
            full_name="Admin User Two",
        )
        self.detective_user = get_user_model().objects.create_user(
            username="detective03",
            email="detective03@example.com",
            password="StrongPass123!",
            phone="09120002002",
            national_id="2000000002",
            full_name="Detective Three",
        )
        self.sergeant_user = get_user_model().objects.create_user(
            username="sergeant01",
            email="sergeant01@example.com",
            password="StrongPass123!",
            phone="09120002003",
            national_id="2000000003",
            full_name="Sergeant One",
        )
        self.officer_user = get_user_model().objects.create_user(
            username="officer03",
            email="officer03@example.com",
            password="StrongPass123!",
            phone="09120002004",
            national_id="2000000004",
            full_name="Officer Three",
        )

        self.detective_token = Token.objects.create(user=self.detective_user)
        self.sergeant_token = Token.objects.create(user=self.sergeant_user)
        self.officer_token = Token.objects.create(user=self.officer_user)

        self.permission_view = Permission.objects.create(
            code="investigation.reasoning.view",
            name="View Reasoning",
            resource="investigation.reasoning",
            action="view",
            description="Can view reasoning submissions",
        )
        self.permission_submit = Permission.objects.create(
            code="investigation.reasoning.submit",
            name="Submit Reasoning",
            resource="investigation.reasoning",
            action="submit",
            description="Can submit detective reasoning",
        )
        self.permission_approve = Permission.objects.create(
            code="investigation.reasoning.approve",
            name="Approve Reasoning",
            resource="investigation.reasoning",
            action="approve",
            description="Can approve or reject detective reasoning",
        )

        self.role_detective = Role.objects.create(key="detective", name="Detective")
        self.role_sergeant = Role.objects.create(key="sergeant", name="Sergeant")
        self.role_officer = Role.objects.create(key="officer", name="Officer")

        RolePermission.objects.create(role=self.role_detective, permission=self.permission_view)
        RolePermission.objects.create(role=self.role_detective, permission=self.permission_submit)
        RolePermission.objects.create(role=self.role_sergeant, permission=self.permission_view)
        RolePermission.objects.create(role=self.role_sergeant, permission=self.permission_approve)

        UserRoleAssignment.objects.create(user=self.detective_user, role=self.role_detective, assigned_by=self.admin_user)
        UserRoleAssignment.objects.create(user=self.sergeant_user, role=self.role_sergeant, assigned_by=self.admin_user)
        UserRoleAssignment.objects.create(user=self.officer_user, role=self.role_officer, assigned_by=self.admin_user)

        self.reasonings_url = "/api/v1/investigation/reasonings/"

    def test_detective_can_submit_reasoning(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.detective_token.key}")
        payload = {
            "case_reference": "CASE-1001",
            "title": "Linking witness testimony",
            "narrative": "This narrative ties evidence A and B.",
        }

        response = self.client.post(self.reasonings_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], "pending")

    def test_user_without_required_permission_cannot_submit_reasoning(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.officer_token.key}")
        payload = {
            "case_reference": "CASE-1002",
            "title": "Officer attempt",
            "narrative": "Should be blocked by RBAC permission check.",
        }

        response = self.client.post(self.reasonings_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "FORBIDDEN")

    def test_sergeant_can_approve_detective_reasoning(self):
        reasoning = ReasoningSubmission.objects.create(
            case_reference="CASE-1003",
            title="Detective submission",
            narrative="Pending detective reasoning",
            submitted_by=self.detective_user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.sergeant_token.key}")

        response = self.client.post(
            f"/api/v1/investigation/reasonings/{reasoning.id}/approve/",
            {"decision": "approved", "justification": "Matches evidence graph"},
            format="json",
        )

        reasoning.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(reasoning.status, ReasoningSubmission.Status.APPROVED)
        self.assertTrue(ReasoningApproval.objects.filter(reasoning=reasoning).exists())

    def test_detective_cannot_approve_reasoning_even_with_approve_permission(self):
        RolePermission.objects.create(role=self.role_detective, permission=self.permission_approve)
        reasoning = ReasoningSubmission.objects.create(
            case_reference="CASE-1004",
            title="Detective submission",
            narrative="Pending detective reasoning",
            submitted_by=self.detective_user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.detective_token.key}")

        response = self.client.post(
            f"/api/v1/investigation/reasonings/{reasoning.id}/approve/",
            {"decision": "approved", "justification": "Should fail role policy"},
            format="json",
        )

        reasoning.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "WORKFLOW_POLICY_VIOLATION")
        self.assertEqual(reasoning.status, ReasoningSubmission.Status.PENDING)

    def test_sergeant_cannot_approve_reasoning_if_submitter_is_not_detective(self):
        reasoning = ReasoningSubmission.objects.create(
            case_reference="CASE-1005",
            title="Officer submission",
            narrative="Pending non-detective reasoning",
            submitted_by=self.officer_user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.sergeant_token.key}")

        response = self.client.post(
            f"/api/v1/investigation/reasonings/{reasoning.id}/approve/",
            {"decision": "approved", "justification": "Should fail workflow submitter policy"},
            format="json",
        )

        reasoning.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "WORKFLOW_POLICY_VIOLATION")
        self.assertEqual(reasoning.status, ReasoningSubmission.Status.PENDING)

    def test_sergeant_reject_requires_rationale(self):
        reasoning = ReasoningSubmission.objects.create(
            case_reference="CASE-1006",
            title="Detective submission",
            narrative="Pending detective reasoning",
            submitted_by=self.detective_user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.sergeant_token.key}")

        response = self.client.post(
            f"/api/v1/investigation/reasonings/{reasoning.id}/approve/",
            {"decision": "rejected"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("justification", response.data.get("error", {}).get("details", {}))
        reasoning.refresh_from_db()
        self.assertEqual(reasoning.status, ReasoningSubmission.Status.PENDING)

    def test_sergeant_can_reject_with_rationale(self):
        reasoning = ReasoningSubmission.objects.create(
            case_reference="CASE-1007",
            title="Detective submission",
            narrative="Pending detective reasoning",
            submitted_by=self.detective_user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.sergeant_token.key}")

        response = self.client.post(
            f"/api/v1/investigation/reasonings/{reasoning.id}/approve/",
            {"decision": "rejected", "justification": "Evidence does not support conclusion."},
            format="json",
        )

        reasoning.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(reasoning.status, ReasoningSubmission.Status.REJECTED)
        approval = ReasoningApproval.objects.get(reasoning=reasoning)
        self.assertEqual(approval.justification, "Evidence does not support conclusion.")

    def test_reasoning_detail_requires_view_permission(self):
        reasoning = ReasoningSubmission.objects.create(
            case_reference="CASE-1008",
            title="Detective submission",
            narrative="Pending",
            submitted_by=self.detective_user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.detective_token.key}")

        response = self.client.get(f"/api/v1/investigation/reasonings/{reasoning.id}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["id"], reasoning.id)
        self.assertEqual(response.data["data"]["case_reference"], "CASE-1008")


class SuspectAssessmentTests(APITestCase):
    """Detective and sergeant scores 1–10 with immutable scoring history."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin_sa",
            email="admin_sa@example.com",
            password="StrongPass123!",
            phone="09120003001",
            national_id="3000000001",
            full_name="Admin SA",
        )
        self.detective_user = get_user_model().objects.create_user(
            username="det_sa",
            email="det_sa@example.com",
            password="StrongPass123!",
            phone="09120003002",
            national_id="3000000002",
            full_name="Detective SA",
        )
        self.sergeant_user = get_user_model().objects.create_user(
            username="sgt_sa",
            email="sgt_sa@example.com",
            password="StrongPass123!",
            phone="09120003003",
            national_id="3000000003",
            full_name="Sergeant SA",
        )
        self.officer_user = get_user_model().objects.create_user(
            username="off_sa",
            email="off_sa@example.com",
            password="StrongPass123!",
            phone="09120003004",
            national_id="3000000004",
            full_name="Officer SA",
        )

        self.detective_token = Token.objects.create(user=self.detective_user)
        self.sergeant_token = Token.objects.create(user=self.sergeant_user)
        self.officer_token = Token.objects.create(user=self.officer_user)

        for code, name, resource, action in [
            ("investigation.suspect_assessment.view", "View", "investigation.suspect_assessment", "view"),
            ("investigation.suspect_assessment.add", "Add", "investigation.suspect_assessment", "add"),
            ("investigation.suspect_assessment.submit_score", "Submit score", "investigation.suspect_assessment", "submit_score"),
        ]:
            Permission.objects.get_or_create(
                code=code,
                defaults={"name": name, "resource": resource, "action": action},
            )

        self.role_detective = Role.objects.get_or_create(key="detective", defaults={"name": "Detective"})[0]
        self.role_sergeant = Role.objects.get_or_create(key="sergeant", defaults={"name": "Sergeant"})[0]
        self.role_officer = Role.objects.get_or_create(key="officer", defaults={"name": "Officer"})[0]

        for perm in Permission.objects.filter(code__startswith="investigation.suspect_assessment."):
            RolePermission.objects.get_or_create(role=self.role_detective, permission=perm)
            RolePermission.objects.get_or_create(role=self.role_sergeant, permission=perm)
        for perm in Permission.objects.filter(code="investigation.suspect_assessment.view"):
            RolePermission.objects.get_or_create(role=self.role_officer, permission=perm)

        UserRoleAssignment.objects.create(user=self.detective_user, role=self.role_detective, assigned_by=self.admin_user)
        UserRoleAssignment.objects.create(user=self.sergeant_user, role=self.role_sergeant, assigned_by=self.admin_user)
        UserRoleAssignment.objects.create(user=self.officer_user, role=self.role_officer, assigned_by=self.admin_user)

        self.case = Case.objects.create(
            title="Test case for assessment",
            summary="Summary",
            level=Case.Level.LEVEL_2,
            source_type=Case.SourceType.COMPLAINT,
            status=Case.Status.SUSPECT_ASSESSMENT,
        )
        self.suspect_participant = CaseParticipant.objects.create(
            case=self.case,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
            role_in_case=CaseParticipant.RoleInCase.SUSPECT,
            full_name="Suspect One",
            national_id="4000000001",
            added_by=self.admin_user,
        )

        self.assessments_url = "/api/v1/investigation/assessments/"

    def test_detective_can_create_assessment_and_submit_score(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.detective_token.key}")
        create_resp = self.client.post(
            self.assessments_url,
            {"case": self.case.id, "participant": self.suspect_participant.id},
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(create_resp.data["success"])
        assessment_id = create_resp.data["data"]["id"]
        self.assertIsNone(create_resp.data["data"]["detective_score"])
        self.assertIsNone(create_resp.data["data"]["sergeant_score"])
        self.assertEqual(len(create_resp.data["data"]["score_entries"]), 0)

        score_resp = self.client.post(
            f"/api/v1/investigation/assessments/{assessment_id}/scores/",
            {"score": 7},
            format="json",
        )
        self.assertEqual(score_resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(score_resp.data["success"])
        self.assertEqual(score_resp.data["data"]["role_key"], "detective")
        self.assertEqual(score_resp.data["data"]["score"], 7)

        detail_resp = self.client.get(f"/api/v1/investigation/assessments/{assessment_id}/", format="json")
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data["data"]["detective_score"], 7)
        self.assertIsNone(detail_resp.data["data"]["sergeant_score"])
        self.assertEqual(len(detail_resp.data["data"]["score_entries"]), 1)

    def test_sergeant_can_submit_score_immutable_history(self):
        assessment = SuspectAssessment.objects.create(case=self.case, participant=self.suspect_participant)
        SuspectAssessmentScoreEntry.objects.create(
            assessment=assessment,
            scored_by=self.detective_user,
            role_key=SuspectAssessmentScoreEntry.RoleKey.DETECTIVE,
            score=6,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.sergeant_token.key}")
        response = self.client.post(
            f"/api/v1/investigation/assessments/{assessment.id}/scores/",
            {"score": 8},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["role_key"], "sergeant")
        self.assertEqual(response.data["data"]["score"], 8)

        detail = self.client.get(f"/api/v1/investigation/assessments/{assessment.id}/", format="json")
        self.assertEqual(detail.data["data"]["detective_score"], 6)
        self.assertEqual(detail.data["data"]["sergeant_score"], 8)
        self.assertEqual(len(detail.data["data"]["score_entries"]), 2)

    def test_score_must_be_1_to_10(self):
        assessment = SuspectAssessment.objects.create(case=self.case, participant=self.suspect_participant)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.detective_token.key}")
        for bad_score, expected_status in [(0, 400), (11, 400)]:
            resp = self.client.post(
                f"/api/v1/investigation/assessments/{assessment.id}/scores/",
                {"score": bad_score},
                format="json",
            )
            self.assertEqual(resp.status_code, expected_status, f"score={bad_score}")
        valid = self.client.post(
            f"/api/v1/investigation/assessments/{assessment.id}/scores/",
            {"score": 10},
            format="json",
        )
        self.assertEqual(valid.status_code, status.HTTP_201_CREATED)

    def test_officer_cannot_submit_score(self):
        assessment = SuspectAssessment.objects.create(case=self.case, participant=self.suspect_participant)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.officer_token.key}")
        response = self.client.post(
            f"/api/v1/investigation/assessments/{assessment.id}/scores/",
            {"score": 5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
