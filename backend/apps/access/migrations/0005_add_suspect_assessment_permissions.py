# Add permissions for suspect assessment (detective/sergeant scores, immutable history)

from django.db import migrations


def create_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    for code, name, resource, action, description in [
        (
            "investigation.suspect_assessment.view",
            "View suspect assessments",
            "investigation.suspect_assessment",
            "view",
            "View suspect assessments and score history.",
        ),
        (
            "investigation.suspect_assessment.add",
            "Add suspect assessment",
            "investigation.suspect_assessment",
            "add",
            "Create a suspect assessment for a case participant (suspect).",
        ),
        (
            "investigation.suspect_assessment.submit_score",
            "Submit suspect assessment score",
            "investigation.suspect_assessment",
            "submit_score",
            "Submit detective or sergeant score (1–10); immutable.",
        ),
    ]:
        Permission.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "resource": resource,
                "action": action,
                "description": description or "",
            },
        )


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(
        code__in=[
            "investigation.suspect_assessment.view",
            "investigation.suspect_assessment.add",
            "investigation.suspect_assessment.submit_score",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0004_add_evidence_review_permission"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
