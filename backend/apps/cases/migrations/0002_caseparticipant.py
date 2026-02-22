import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CaseParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('participant_kind', models.CharField(choices=[('personnel', 'Personnel'), ('civilian', 'Civilian')], max_length=20)),
                ('role_in_case', models.CharField(choices=[('complainant', 'Complainant'), ('witness', 'Witness'), ('suspect', 'Suspect'), ('judge', 'Judge'), ('cadet', 'Cadet'), ('police_officer', 'Police Officer'), ('detective', 'Detective'), ('sergeant', 'Sergeant'), ('captain', 'Captain'), ('chief', 'Chief'), ('coroner', 'Coroner'), ('base_user', 'Base User')], max_length=30)),
                ('full_name', models.CharField(blank=True, max_length=255)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('national_id', models.CharField(blank=True, max_length=32)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='case_participants_added', to=settings.AUTH_USER_MODEL)),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='cases.case')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='case_participations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['case', 'role_in_case'], name='cases_casep_case_id_3a130c_idx'), models.Index(fields=['participant_kind'], name='cases_casep_partici_5f3c7a_idx'), models.Index(fields=['user'], name='cases_casep_user_id_39896b_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(('user__isnull', False), models.Q(('full_name', ''), _negated=True), _connector='OR'), name='cases_caseparticipant_user_or_full_name'), models.UniqueConstraint(condition=models.Q(('user__isnull', False)), fields=('case', 'role_in_case', 'user'), name='cases_caseparticipant_unique_case_role_user'), models.UniqueConstraint(condition=models.Q(('user__isnull', True), models.Q(('national_id', ''), _negated=True)), fields=('case', 'role_in_case', 'national_id'), name='cases_caseparticipant_unique_case_role_national_id')],
            },
        ),
    ]
