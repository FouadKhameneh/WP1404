from django.db import migrations


def create_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.get_or_create(
        code="reports.view",
        defaults={
            "name": "View reports",
            "resource": "reports",
            "action": "view",
            "description": "View reporting and statistics APIs.",
        },
    )


def remove_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(code="reports.view").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0011_add_payment_initiate_permission"),
    ]

    operations = [
        migrations.RunPython(create_permission, remove_permission),
    ]
