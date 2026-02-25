# Generated migration to add permissions for case timeline/suspect/status transition APIs

from django.db import migrations


def create_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.get_or_create(
        code="cases.suspects.add",
        defaults={
            "name": "Add Suspect",
            "resource": "cases.suspects",
            "action": "add",
        },
    )
    Permission.objects.get_or_create(
        code="cases.case.transition_status",
        defaults={
            "name": "Transition Case Status",
            "resource": "cases.case",
            "action": "transition_status",
        },
    )


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(code__in=["cases.suspects.add", "cases.case.transition_status"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
