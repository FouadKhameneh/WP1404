from django.conf import settings
from django.db import models


class CaseVerdict(models.Model):
    """Judge trial verdict and punishment recording. One per case when closed after trial."""

    class Verdict(models.TextChoices):
        GUILTY = "guilty", "Guilty"
        NOT_GUILTY = "not_guilty", "Not Guilty"

    case = models.OneToOneField(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="verdict",
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_verdicts",
    )
    verdict = models.CharField(max_length=20, choices=Verdict.choices)
    punishment_title = models.CharField(max_length=200, blank=True)
    punishment_description = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["verdict"])]
        verbose_name = "Case Verdict"
        verbose_name_plural = "Case Verdicts"

    def __str__(self):
        return f"{self.case_id}:{self.verdict}"
