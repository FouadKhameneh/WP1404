# Generated migration to add permission for case list/detail APIs

from django.db import migrations


def create_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.get_or_create(
        code="cases.cases.view",
        defaults={
            "name": "View Cases",
            "resource": "cases.cases",
            "action": "view",
        },
    )


def remove_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(code="cases.cases.view").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0002_add_case_timeline_permissions"),
    ]

    operations = [
        migrations.RunPython(create_permission, remove_permission),
    ]
