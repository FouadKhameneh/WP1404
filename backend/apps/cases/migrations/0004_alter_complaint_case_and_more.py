import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0003_complaint_complaintreview_complaintvalidationcounter_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='complaint',
            name='case',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to='cases.case'),
        ),
        migrations.AddConstraint(
            model_name='complaint',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('status', 'validated'), _negated=True), ('case__isnull', False), _connector='OR'), name='cases_complaint_validated_requires_case'),
        ),
    ]
