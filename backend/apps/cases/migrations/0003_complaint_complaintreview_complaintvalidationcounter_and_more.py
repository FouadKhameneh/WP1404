import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0002_caseparticipant'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('cadet_review', 'Cadet Review'), ('validated', 'Validated'), ('rejected', 'Rejected'), ('final_invalid', 'Final Invalid')], default='submitted', max_length=20)),
                ('rejection_reason', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('validated_at', models.DateTimeField(blank=True, null=True)),
                ('invalidated_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to='cases.case')),
                ('complainant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='complaints_submitted', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ComplaintReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('decision', models.CharField(choices=[('approved', 'Approved'), ('rejected', 'Rejected')], max_length=20)),
                ('rejection_reason', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(auto_now_add=True)),
                ('complaint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='cases.complaint')),
                ('reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='complaint_reviews', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ComplaintValidationCounter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invalid_attempt_count', models.PositiveSmallIntegerField(default=0)),
                ('last_rejection_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('complaint', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='validation_counter', to='cases.complaint')),
            ],
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['case', 'status'], name='cases_compl_case_id_ff64f0_idx'),
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['complainant'], name='cases_compl_complai_dd3107_idx'),
        ),
        migrations.AddConstraint(
            model_name='complaint',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('status', 'final_invalid'), _negated=True), ('invalidated_at__isnull', False), _connector='OR'), name='cases_complaint_final_invalid_requires_invalidated_at'),
        ),
        migrations.AddConstraint(
            model_name='complaint',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('status', 'validated'), _negated=True), ('validated_at__isnull', False), _connector='OR'), name='cases_complaint_validated_requires_validated_at'),
        ),
        migrations.AddIndex(
            model_name='complaintreview',
            index=models.Index(fields=['complaint', 'reviewed_at'], name='cases_compl_complai_b1635e_idx'),
        ),
        migrations.AddIndex(
            model_name='complaintreview',
            index=models.Index(fields=['decision'], name='cases_compl_decisio_37db73_idx'),
        ),
        migrations.AddConstraint(
            model_name='complaintreview',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('decision', 'rejected'), _negated=True), models.Q(('rejection_reason', ''), _negated=True), _connector='OR'), name='cases_complaintreview_rejected_requires_reason'),
        ),
        migrations.AddConstraint(
            model_name='complaintvalidationcounter',
            constraint=models.CheckConstraint(condition=models.Q(('invalid_attempt_count__gte', 0), ('invalid_attempt_count__lte', 3)), name='cases_complaintcounter_attempt_count_between_0_3'),
        ),
    ]
