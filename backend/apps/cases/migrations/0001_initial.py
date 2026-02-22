import apps.cases.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('case_number', models.CharField(default=apps.cases.models.generate_case_number, editable=False, max_length=32, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('summary', models.TextField(blank=True)),
                ('level', models.CharField(choices=[('1', 'Level 1'), ('2', 'Level 2'), ('3', 'Level 3'), ('critical', 'Critical')], max_length=10)),
                ('source_type', models.CharField(choices=[('complaint', 'Complaint'), ('scene_report', 'Scene Report')], max_length=20)),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('under_review', 'Under Review'), ('active_investigation', 'Active Investigation'), ('suspect_assessment', 'Suspect Assessment'), ('referral_ready', 'Referral Ready'), ('in_trial', 'In Trial'), ('closed', 'Closed'), ('final_invalid', 'Final Invalid')], default='submitted', max_length=30)),
                ('priority', models.CharField(blank=True, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], max_length=10)),
                ('assigned_role_key', models.CharField(blank=True, max_length=100)),
                ('assignment_notes', models.TextField(blank=True)),
                ('assigned_at', models.DateTimeField(blank=True, null=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('under_review_at', models.DateTimeField(blank=True, null=True)),
                ('investigation_started_at', models.DateTimeField(blank=True, null=True)),
                ('suspect_assessed_at', models.DateTimeField(blank=True, null=True)),
                ('referral_ready_at', models.DateTimeField(blank=True, null=True)),
                ('trial_started_at', models.DateTimeField(blank=True, null=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='case_assignments_made', to=settings.AUTH_USER_MODEL)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_cases', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cases_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['status'], name='cases_case_status_5f99d2_idx'), models.Index(fields=['level'], name='cases_case_level_2ba0d7_idx'), models.Index(fields=['priority'], name='cases_case_priorit_474e7d_idx'), models.Index(fields=['source_type'], name='cases_case_source__2d354f_idx'), models.Index(fields=['assigned_to'], name='cases_case_assigne_8931bc_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(models.Q(('closed_at__isnull', False), ('status', 'closed')), models.Q(('status', 'closed'), _negated=True), _connector='OR'), name='cases_case_closed_requires_closed_at')],
            },
        ),
    ]
