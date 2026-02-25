from django.db import migrations


def create_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.get_or_create(
        code="wanted.view",
        defaults={
            "name": "View wanted",
            "resource": "wanted",
            "action": "view",
            "description": "View wanted and most wanted lists.",
        },
    )


def remove_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(code="wanted.view").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0007_add_judiciary_permissions"),
    ]

    operations = [
        migrations.RunPython(create_permission, remove_permission),
    ]
