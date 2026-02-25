from django.db import migrations


def create_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    for code, name, resource, action in [
        ("rewards.tip.view", "View reward tips", "rewards.tip", "view"),
        ("rewards.tip.submit", "Submit reward tip", "rewards.tip", "submit"),
        ("rewards.tip.review", "Review reward tip", "rewards.tip", "review"),
    ]:
        Permission.objects.get_or_create(
            code=code,
            defaults={"name": name, "resource": resource, "action": action, "description": ""},
        )


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(
        code__in=["rewards.tip.view", "rewards.tip.submit", "rewards.tip.review"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0008_add_wanted_view_permission"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
