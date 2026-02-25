# Arrest and interrogation order permissions (sergeant-only context)

from django.db import migrations


def create_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    for code, name, resource, action, description in [
        ("investigation.arrest_order.view", "View arrest orders", "investigation.arrest_order", "view", "List and view arrest orders (sergeant)."),
        ("investigation.arrest_order.add", "Add arrest order", "investigation.arrest_order", "add", "Issue arrest order (sergeant)."),
        ("investigation.arrest_order.change", "Change arrest order", "investigation.arrest_order", "change", "Update arrest order status (sergeant)."),
        ("investigation.interrogation_order.view", "View interrogation orders", "investigation.interrogation_order", "view", "List and view interrogation orders (sergeant)."),
        ("investigation.interrogation_order.add", "Add interrogation order", "investigation.interrogation_order", "add", "Issue interrogation order (sergeant)."),
        ("investigation.interrogation_order.change", "Change interrogation order", "investigation.interrogation_order", "change", "Update interrogation order status (sergeant)."),
    ]:
        Permission.objects.get_or_create(
            code=code,
            defaults={"name": name, "resource": resource, "action": action, "description": description or ""},
        )


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model("access", "Permission")
    Permission.objects.filter(
        code__in=[
            "investigation.arrest_order.view",
            "investigation.arrest_order.add",
            "investigation.arrest_order.change",
            "investigation.interrogation_order.view",
            "investigation.interrogation_order.add",
            "investigation.interrogation_order.change",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0005_add_suspect_assessment_permissions"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
