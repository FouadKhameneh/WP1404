
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.notifications.models import AuditLog, TimelineEvent


class AuditTrailInfrastructureTests(APITestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin03",
            email="admin03@example.com",
            password="StrongPass123!",
            phone="09120003001",
            national_id="3000000001",
            full_name="Admin User Three",
        )
        self.admin_token = Token.objects.create(user=self.admin_user)

    def test_register_logs_audit_and_timeline_with_redacted_payload(self):
        payload = {
            "username": "citizen01",
            "email": "citizen01@example.com",
            "phone": "09120003002",
            "national_id": "3000000002",
            "full_name": "Citizen One",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        response = self.client.post("/api/v1/identity/auth/register/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        audit = AuditLog.objects.latest("id")
        self.assertEqual(audit.request_method, "POST")
        self.assertEqual(audit.request_path, "/api/v1/identity/auth/register/")
        self.assertEqual(audit.target_type, "identity.auth")
        self.assertEqual(audit.status_code, status.HTTP_201_CREATED)
        self.assertEqual(audit.payload_summary["data"]["password"], "[REDACTED]")
        self.assertEqual(audit.payload_summary["data"]["national_id"], "[REDACTED]")

        timeline = TimelineEvent.objects.filter(event_type="identity.user.registered").latest("id")
        self.assertEqual(timeline.target_type, "identity.user")
        self.assertTrue(timeline.target_id)

    def test_role_patch_logs_actor_target_and_payload_summary(self):
        role = Role.objects.create(key="captain", name="Captain")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        response = self.client.patch(
            f"/api/v1/access/roles/{role.id}/",
            {"description": "Updated captain role"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        audit = AuditLog.objects.filter(request_path=f"/api/v1/access/roles/{role.id}/").latest("id")
        self.assertEqual(audit.actor_id, self.admin_user.id)
        self.assertEqual(audit.target_type, "access.roles")
        self.assertEqual(audit.target_id, str(role.id))
        self.assertEqual(audit.payload_summary["data"]["description"], "Updated captain role")

        timeline = TimelineEvent.objects.filter(event_type="access.role.updated").latest("id")
        self.assertEqual(timeline.actor_id, self.admin_user.id)
        self.assertEqual(timeline.target_id, str(role.id))

    def test_reasoning_approval_creates_workflow_timeline_event(self):
        detective_user = get_user_model().objects.create_user(
            username="detective04",
            email="detective04@example.com",
            password="StrongPass123!",
            phone="09120003003",
            national_id="3000000003",
            full_name="Detective Four",
        )
        sergeant_user = get_user_model().objects.create_user(
            username="sergeant02",
            email="sergeant02@example.com",
            password="StrongPass123!",
            phone="09120003004",
            national_id="3000000004",
            full_name="Sergeant Two",
        )
        detective_token = Token.objects.create(user=detective_user)
        sergeant_token = Token.objects.create(user=sergeant_user)

        permission_view = Permission.objects.create(
            code="investigation.reasoning.view",
            name="View Reasoning",
            resource="investigation.reasoning",
            action="view",
            description="Can view reasoning submissions",
        )
        permission_submit = Permission.objects.create(
            code="investigation.reasoning.submit",
            name="Submit Reasoning",
            resource="investigation.reasoning",
            action="submit",
            description="Can submit reasoning",
        )
        permission_approve = Permission.objects.create(
            code="investigation.reasoning.approve",
            name="Approve Reasoning",
            resource="investigation.reasoning",
            action="approve",
            description="Can approve reasoning",
        )

        detective_role = Role.objects.create(key="detective", name="Detective")
        sergeant_role = Role.objects.create(key="sergeant", name="Sergeant")
        RolePermission.objects.create(role=detective_role, permission=permission_view)
        RolePermission.objects.create(role=detective_role, permission=permission_submit)
        RolePermission.objects.create(role=sergeant_role, permission=permission_view)
        RolePermission.objects.create(role=sergeant_role, permission=permission_approve)
        UserRoleAssignment.objects.create(user=detective_user, role=detective_role, assigned_by=self.admin_user)
        UserRoleAssignment.objects.create(user=sergeant_user, role=sergeant_role, assigned_by=self.admin_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {detective_token.key}")
        create_response = self.client.post(
            "/api/v1/investigation/reasonings/",
            {
                "case_reference": "CASE-9001",
                "title": "Reasoning Draft",
                "narrative": "Detective draft",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        reasoning_id = create_response.data["data"]["id"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {sergeant_token.key}")
        approve_response = self.client.post(
            f"/api/v1/investigation/reasonings/{reasoning_id}/approve/",
            {"decision": "approved", "justification": "Consistent with evidence"},
            format="json",
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)

        timeline = TimelineEvent.objects.filter(event_type="investigation.reasoning.approved").latest("id")
        self.assertEqual(timeline.actor_id, sergeant_user.id)
        self.assertEqual(timeline.target_id, str(reasoning_id))
        self.assertEqual(timeline.case_reference, "CASE-9001")

        audit = AuditLog.objects.filter(request_path=f"/api/v1/investigation/reasonings/{reasoning_id}/approve/").latest(
            "id"
        )
        self.assertEqual(audit.actor_id, sergeant_user.id)
        self.assertEqual(audit.status_code, status.HTTP_200_OK)


class ScheduledTasksTests(APITestCase):
    """Tests for async/scheduler management commands (task 42)."""

    def test_run_scheduled_tasks_dry_run_completes_without_error(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("run_scheduled_tasks", "--dry-run", stdout=out)
        self.assertIn("All scheduled tasks completed", out.getvalue())

    def test_expire_tokens_dry_run_completes_without_error(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("expire_tokens", "--dry-run", stdout=out)
        self.assertIn("token", out.getvalue().lower())

    def test_payment_reconcile_dry_run_completes_without_error(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("payment_reconcile", "--dry-run", stdout=out)
        self.assertIn("transaction", out.getvalue().lower())
