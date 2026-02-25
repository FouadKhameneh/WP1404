from datetime import timedelta

from django.utils import timezone

from apps.wanted.models import Wanted


def promote_to_most_wanted():
    """Promote Wanted to Most Wanted when marked_at is more than one month ago. Idempotent."""
    threshold = timezone.now() - timedelta(days=30)
    updated = Wanted.objects.filter(
        status=Wanted.Status.WANTED,
        marked_at__lte=threshold,
    ).update(status=Wanted.Status.MOST_WANTED, promoted_at=timezone.now())
    return updated
