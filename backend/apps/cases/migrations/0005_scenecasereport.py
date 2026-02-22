import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0004_alter_complaint_case_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SceneCaseReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scene_occurred_at', models.DateTimeField()),
                ('reported_at', models.DateTimeField(auto_now_add=True)),
                ('superior_approval_required', models.BooleanField(default=True)),
                ('superior_approved_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('case', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scene_report_detail', to='cases.case')),
                ('reported_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scene_cases_reported', to=settings.AUTH_USER_MODEL)),
                ('superior_approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scene_case_approvals', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['scene_occurred_at'], name='cases_scene_scene_o_fecadc_idx'), models.Index(fields=['reported_by'], name='cases_scene_reporte_0ac61d_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(models.Q(('superior_approved_at__isnull', True), ('superior_approved_by__isnull', True)), models.Q(('superior_approved_at__isnull', False), ('superior_approved_by__isnull', False)), _connector='OR'), name='cases_scenecasereport_approval_actor_time_consistent')],
            },
        ),
    ]
