# Generated migration to add permission for biological evidence coroner review

from django.db import migrations


def create_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.get_or_create(
        code="evidence.biological_medical.review",
        defaults={
            "name": "Review biological/medical evidence",
            "resource": "evidence",
            "action": "biological_medical.review",
            "description": "Submit coroner accept/reject decision and follow-up notes for biological/medical evidence.",
        },
    )


def remove_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(code="evidence.biological_medical.review").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0003_add_case_list_detail_permission"),
    ]

    operations = [
        migrations.RunPython(create_permission, remove_permission),
    ]
