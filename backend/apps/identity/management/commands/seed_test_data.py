"""
Management command to seed test data for development and demo.
Creates roles, permissions, users, cases, evidence, wanted, and reward tips.
Run: python manage.py seed_test_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.access.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.cases.models import Case, CaseParticipant, Complaint, SceneCaseReport
from apps.evidence.models import (
    BiologicalMedicalEvidence,
    IdentificationEvidence,
    OtherEvidence,
    VehicleEvidence,
    WitnessTestimony,
)
from apps.identity.models import User
from apps.rewards.models import RewardTip, generate_reward_claim_id
from apps.wanted.models import Wanted


class Command(BaseCommand):
    help = "Seed test data: roles, users, cases, evidence, wanted, rewards"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing test data before seeding")
        parser.add_argument("--no-superuser", action="store_true", help="Skip creating admin superuser")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_test_data()

        self.stdout.write("Seeding roles and permissions...")
        roles = self._ensure_roles_and_permissions()

        self.stdout.write("Seeding users...")
        users = self._ensure_users(roles, create_superuser=not options["no_superuser"])

        self.stdout.write("Seeding cases...")
        cases = self._ensure_cases(users)

        self.stdout.write("Seeding evidence...")
        self._ensure_evidence(cases, users)

        self.stdout.write("Seeding wanted entries...")
        self._ensure_wanted(cases, users)

        self.stdout.write("Seeding reward tips...")
        self._ensure_reward_tips(users)

        self.stdout.write(self.style.SUCCESS("Test data seeded successfully."))
        self._print_credentials(users)

    def _clear_test_data(self):
        Wanted.objects.all().delete()
        RewardTip.objects.all().delete()
        BiologicalMedicalEvidence.objects.all().delete()
        WitnessTestimony.objects.all().delete()
        VehicleEvidence.objects.all().delete()
        IdentificationEvidence.objects.all().delete()
        OtherEvidence.objects.all().delete()
        Complaint.objects.all().delete()
        SceneCaseReport.objects.all().delete()
        CaseParticipant.objects.all().delete()
        Case.objects.all().delete()
        UserRoleAssignment.objects.all().delete()
        RolePermission.objects.all().delete()
        for u in User.objects.exclude(username="admin"):
            u.delete()
        self.stdout.write("Cleared existing test data.")

    def _ensure_roles_and_permissions(self):
        perms = {p.code: p for p in Permission.objects.all()}
        role_keys = ["admin", "detective", "sergeant", "captain", "coroner", "cadet", "police_officer", "complainant", "judge"]
        role_names = {
            "admin": "مدیر سیستم",
            "detective": "کارآگاه",
            "sergeant": "گروهبان",
            "captain": "کاپیتان",
            "coroner": "پزشک قانونی",
            "cadet": "کارآموز",
            "police_officer": "افسر پلیس",
            "complainant": "شاکی",
            "judge": "قاضی",
        }
        roles = {}
        for key in role_keys:
            r, _ = Role.objects.get_or_create(key=key, defaults={"name": role_names.get(key, key)})
            roles[key] = r

        all_perms = list(perms.values())
        for r in roles.values():
            for p in all_perms:
                RolePermission.objects.get_or_create(role=r, permission=p)

        return roles

    def _ensure_users(self, roles, create_superuser=True):
        users = {}
        base_pass = "test1234"
        if create_superuser:
            admin, _ = User.objects.get_or_create(
                username="admin",
                defaults={
                    "email": "admin@test.local",
                    "phone": "09120000000",
                    "national_id": "0000000000",
                    "full_name": "مدیر سیستم",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            admin.set_password("admin123")
            admin.save()
            users["admin"] = admin
            ura, _ = UserRoleAssignment.objects.get_or_create(user=admin, role=roles["admin"], defaults={"assigned_by": admin})
            if _:
                ura.assigned_by = admin
                ura.save()

        test_users = [
            ("detective1", "کارآگاه اول", "09121111111", "1111111111", "detective"),
            ("sergeant1", "گروهبان اول", "09122222222", "2222222222", "sergeant"),
            ("captain1", "کاپیتان اول", "09123333333", "3333333333", "captain"),
            ("coroner1", "پزشک قانونی", "09124444444", "4444444444", "coroner"),
            ("cadet1", "کارآموز اول", "09125555555", "5555555555", "cadet"),
            ("officer1", "افسر پلیس", "09126666666", "6666666666", "police_officer"),
            ("shaki1", "شاکی نمونه", "09127777777", "7777777777", "complainant"),
            ("judge1", "قاضی نمونه", "09128888888", "8888888888", "judge"),
        ]
        for username, full_name, phone, national_id, role_key in test_users:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@test.local",
                    "phone": phone,
                    "national_id": national_id,
                    "full_name": full_name,
                },
            )
            if created:
                u.set_password(base_pass)
                u.save()
            users[username] = u
            role = roles.get(role_key)
            if role:
                assiger = users.get("admin") or u
                UserRoleAssignment.objects.get_or_create(user=u, role=role, defaults={"assigned_by": assiger})

        return users

    def _ensure_cases(self, users):
        cases = []
        detective = users.get("detective1")
        officer = users.get("officer1")
        complainant = users.get("shaki1")
        now = timezone.now()

        case1, _ = Case.objects.get_or_create(
            case_number="CASE-SEED-001",
            defaults={
                "title": "سرقت مغازه خیابان اصلی",
                "summary": "پرونده نمونه سرقت از مغازه در خیابان اصلی",
                "level": Case.Level.LEVEL_2,
                "source_type": Case.SourceType.COMPLAINT,
                "status": Case.Status.ACTIVE_INVESTIGATION,
                "priority": Case.Priority.MEDIUM,
                "created_by": detective,
                "assigned_to": detective,
                "submitted_at": now,
            },
        )
        cases.append(case1)
        CaseParticipant.objects.get_or_create(
            case=case1,
            role_in_case=CaseParticipant.RoleInCase.DETECTIVE,
            user=detective,
            defaults={"participant_kind": CaseParticipant.ParticipantKind.PERSONNEL, "full_name": detective.full_name},
        )
        CaseParticipant.objects.get_or_create(
            case=case1,
            role_in_case=CaseParticipant.RoleInCase.COMPLAINANT,
            user=complainant,
            defaults={"participant_kind": CaseParticipant.ParticipantKind.CIVILIAN, "full_name": complainant.full_name},
        )

        case2, _ = Case.objects.get_or_create(
            case_number="CASE-SEED-002",
            defaults={
                "title": "صحنه جرم تصادف",
                "summary": "گزارش صحنه جرم تصادف در بزرگراه",
                "level": Case.Level.LEVEL_3,
                "source_type": Case.SourceType.SCENE_REPORT,
                "status": Case.Status.UNDER_REVIEW,
                "priority": Case.Priority.MEDIUM,
                "created_by": officer,
                "assigned_to": officer,
                "submitted_at": now,
            },
        )
        cases.append(case2)
        SceneCaseReport.objects.get_or_create(
            case=case2,
            defaults={
                "reported_by": officer,
                "scene_occurred_at": now,
                "superior_approval_required": True,
            },
        )
        CaseParticipant.objects.get_or_create(
            case=case2,
            role_in_case=CaseParticipant.RoleInCase.POLICE_OFFICER,
            user=officer,
            defaults={"participant_kind": CaseParticipant.ParticipantKind.PERSONNEL, "full_name": officer.full_name},
        )

        case3, _ = Case.objects.get_or_create(
            case_number="CASE-SEED-003",
            defaults={
                "title": "پرونده حل‌شده نمونه",
                "summary": "پرونده بسته شده برای تست",
                "level": Case.Level.LEVEL_3,
                "source_type": Case.SourceType.COMPLAINT,
                "status": Case.Status.CLOSED,
                "priority": Case.Priority.LOW,
                "created_by": detective,
                "closed_at": now,
                "submitted_at": now,
            },
        )
        cases.append(case3)

        return cases

    def _ensure_evidence(self, cases, users):
        detective = users.get("detective1")
        coroner_user = users.get("coroner1")
        now = timezone.now()

        if cases:
            case = cases[0]
            WitnessTestimony.objects.get_or_create(
                case=case,
                title="اظهارات شاهد اول",
                defaults={
                    "description": "گواهی شاهد عینی از صحنه",
                    "transcript": "من شاهد سرقت بودم...",
                    "registered_at": now,
                    "registrar": detective,
                },
            )
            OtherEvidence.objects.get_or_create(
                case=case,
                title="مدرک دیگر - یادداشت",
                defaults={
                    "description": "یادداشت یافت شده در صحنه",
                    "registered_at": now,
                    "registrar": detective,
                },
            )
            VehicleEvidence.objects.get_or_create(
                case=case,
                title="خودرو مشکوک",
                defaults={
                    "description": "خودروی مشاهده شده در صحنه",
                    "model": "پژو ۲۰۶",
                    "color": "سفید",
                    "plate": "۱۲-الف-۳۴۵-ایران۶۷",
                    "serial_number": "",
                    "registered_at": now,
                    "registrar": detective,
                },
            )
            IdentificationEvidence.objects.get_or_create(
                case=case,
                title="کارت شناسایی یافت شده",
                defaults={
                    "description": "مدرک شناسایی در صحنه",
                    "attributes": {"full_name": "شخص نمونه", "national_id": "1234567890"},
                    "registered_at": now,
                    "registrar": detective,
                },
            )
            bio, _ = BiologicalMedicalEvidence.objects.get_or_create(
                case=case,
                title="نمونه خون",
                defaults={
                    "description": "شواهد زیست‌شناسی یافت شده",
                    "registered_at": now,
                    "registrar": detective,
                    "coroner_status": BiologicalMedicalEvidence.CoronerStatus.PENDING,
                },
            )
            if case == cases[0]:
                BiologicalMedicalEvidence.objects.get_or_create(
                    case=case,
                    title="اثر انگشت",
                    defaults={
                        "description": "اثر انگشت از صحنه",
                        "registered_at": now,
                        "registrar": detective,
                        "coroner_status": BiologicalMedicalEvidence.CoronerStatus.RESULT_RECEIVED,
                        "coroner": coroner_user,
                        "coroner_result": "تطابق با بانک داده تایید شد",
                    },
                )

    def _ensure_wanted(self, cases, users):
        if not cases:
            return
        case = cases[0]
        partic = CaseParticipant.objects.filter(case=case, role_in_case=CaseParticipant.RoleInCase.SUSPECT).first()
        if not partic:
            detective = users.get("detective1")
            partic, _ = CaseParticipant.objects.get_or_create(
                case=case,
                role_in_case=CaseParticipant.RoleInCase.SUSPECT,
                defaults={
                    "participant_kind": CaseParticipant.ParticipantKind.CIVILIAN,
                    "full_name": "مظنون تحت تعقیب",
                    "national_id": "9999999999",
                    "added_by": detective,
                },
            )
        Wanted.objects.get_or_create(
            case=case,
            participant=partic,
            defaults={"status": Wanted.Status.MOST_WANTED},
        )

    def _ensure_reward_tips(self, users):
        complainant = users.get("shaki1")
        officer = users.get("officer1")
        RewardTip.objects.get_or_create(
            submitted_by=complainant,
            case_reference="CASE-SEED-001",
            subject="اطلاعات در مورد مظنون",
            defaults={"content": "اطلاعات مفید برای شناسایی مظنون", "reward_claim_id": generate_reward_claim_id()},
        )
        RewardTip.objects.get_or_create(
            submitted_by=officer,
            case_reference="CASE-SEED-002",
            subject="نکته افسر",
            defaults={"content": "اطلاعات تکمیلی از صحنه", "reward_claim_id": generate_reward_claim_id()},
        )

    def _print_credentials(self, users):
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Test credentials:")
        self.stdout.write("  admin / admin123")
        self.stdout.write("  detective1 / test1234")
        self.stdout.write("  sergeant1 / test1234")
        self.stdout.write("  shaki1 / test1234")
        self.stdout.write("  ... (others use test1234)")
        self.stdout.write("=" * 50)
