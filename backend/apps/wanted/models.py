from django.conf import settings
from django.db import models
from django.utils import timezone


class Wanted(models.Model):
    """Wanted lifecycle: on suspect mark -> Wanted; scheduled promotion to Most Wanted after one month."""

    class Status(models.TextChoices):
        WANTED = "wanted", "Wanted"
        MOST_WANTED = "most_wanted", "Most Wanted"

    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="wanted_entries",
    )
    participant = models.ForeignKey(
        "cases.CaseParticipant",
        on_delete=models.CASCADE,
        related_name="wanted_entries",
    )
    marked_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WANTED)
    promoted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case", "participant"],
                name="wanted_unique_case_participant",
            ),
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["marked_at"]),
        ]
        ordering = ["-marked_at"]

    def __str__(self):
        return f"Wanted case={self.case_id} participant={self.participant_id} ({self.status})"
