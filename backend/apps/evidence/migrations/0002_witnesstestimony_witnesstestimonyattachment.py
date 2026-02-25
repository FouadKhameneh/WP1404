import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidence", "0001_initial_evidence"),
    ]

    operations = [
        migrations.CreateModel(
            name="WitnessTestimony",
            fields=[
                (
                    "evidence_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="evidence.evidence",
                    ),
                ),
                ("transcript", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Witness Testimony",
                "verbose_name_plural": "Witness Testimonies",
            },
            bases=("evidence.evidence",),
        ),
        migrations.CreateModel(
            name="WitnessTestimonyAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="evidence/witness_testimony/")),
                (
                    "media_type",
                    models.CharField(
                        choices=[("image", "Image"), ("video", "Video"), ("audio", "Audio")],
                        db_index=True,
                        max_length=10,
                    ),
                ),
                (
                    "duration_seconds",
                    models.PositiveIntegerField(blank=True, help_text="Duration in seconds (video/audio)", null=True),
                ),
                ("width", models.PositiveIntegerField(blank=True, null=True)),
                ("height", models.PositiveIntegerField(blank=True, null=True)),
                ("file_size", models.PositiveBigIntegerField(blank=True, help_text="Size in bytes", null=True)),
                ("mime_type", models.CharField(blank=True, max_length=100)),
                ("caption", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "witness_testimony",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="evidence.witnesstestimony",
                    ),
                ),
            ],
            options={
                "verbose_name": "Witness Testimony Attachment",
                "verbose_name_plural": "Witness Testimony Attachments",
                "ordering": ["created_at"],
            },
        ),
    ]
