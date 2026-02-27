# Generated migration for evidence CRUD permissions

from django.db import migrations


def create_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.get_or_create(
        code="evidence.cases.view",
        defaults={
            "name": "View case evidence",
            "resource": "evidence",
            "action": "cases.view",
            "description": "View evidence list and details for cases.",
        },
    )
    Permission.objects.get_or_create(
        code="evidence.create",
        defaults={
            "name": "Create evidence",
            "resource": "evidence",
            "action": "create",
            "description": "Add new evidence (witness, biological, vehicle, identification, other) to cases.",
        },
    )


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(code__in=["evidence.cases.view", "evidence.create"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0012_add_reports_view_permission"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
