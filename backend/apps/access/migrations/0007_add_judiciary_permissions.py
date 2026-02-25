from django.db import migrations


def create_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    for code, name, resource, action, description in [
        ("judiciary.referral.view", "View referral package", "judiciary.referral", "view", "View referral package for case."),
        ("judiciary.verdict.view", "View verdict", "judiciary.verdict", "view", "View recorded verdict."),
        ("judiciary.verdict.add", "Record verdict", "judiciary.verdict", "add", "Judge records verdict and punishment."),
    ]:
        Permission.objects.get_or_create(
            code=code,
            defaults={"name": name, "resource": resource, "action": action, "description": description or ""},
        )


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(
        code__in=["judiciary.referral.view", "judiciary.verdict.view", "judiciary.verdict.add"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0006_add_arrest_interrogation_order_permissions"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
