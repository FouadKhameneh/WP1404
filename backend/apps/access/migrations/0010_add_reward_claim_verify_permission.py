from django.db import migrations


def create_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.get_or_create(
        code="rewards.claim.verify",
        defaults={
            "name": "Verify reward claim",
            "resource": "rewards.claim",
            "action": "verify",
            "description": "Verify reward claim by National ID + Unique ID (authorized police ranks).",
        },
    )


def remove_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(code="rewards.claim.verify").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0009_add_reward_tip_permissions"),
    ]

    operations = [
        migrations.RunPython(create_permission, remove_permission),
    ]
