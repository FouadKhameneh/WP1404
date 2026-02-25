from django.db import migrations


def create_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.get_or_create(
        code="payments.initiate",
        defaults={
            "name": "Initiate payment",
            "resource": "payments",
            "action": "initiate",
            "description": "Initiate level 2/3 bail/fine payment.",
        },
    )


def remove_permission(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(code="payments.initiate").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0010_add_reward_claim_verify_permission"),
    ]

    operations = [
        migrations.RunPython(create_permission, remove_permission),
    ]
