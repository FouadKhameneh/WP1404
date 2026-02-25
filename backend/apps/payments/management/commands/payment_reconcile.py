"""Scheduled task: reconcile pending payments (mark stale pending as failed)."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.payments.models import PaymentTransaction


class Command(BaseCommand):
    help = "Mark pending payment transactions older than N days as failed (scheduler task)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Pending transactions older than this many days are marked failed (default: 7).",
        )
        parser.add_argument("--dry-run", action="store_true", help="Only report what would be updated.")

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(days=days)
        qs = PaymentTransaction.objects.filter(status=PaymentTransaction.Status.PENDING, created_at__lt=cutoff)
        count = qs.count()
        if not dry_run and count:
            qs.update(status=PaymentTransaction.Status.FAILED)
        if dry_run:
            self.stdout.write(self.style.WARNING(f"Would mark {count} pending transaction(s) as failed (older than {days} days)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Marked {count} pending transaction(s) as failed (older than {days} days)."))
