"""Scheduled task: expire (delete) auth tokens for users inactive beyond max age."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from rest_framework.authtoken.models import Token

User = get_user_model()


class Command(BaseCommand):
    help = "Expire auth tokens for users who have not logged in for more than N days (scheduler task)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Expire tokens for users with last_login older than this many days (default: 90).",
        )
        parser.add_argument("--dry-run", action="store_true", help="Only report what would be deleted.")

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(days=days)
        user_ids = list(Token.objects.values_list("user_id", flat=True).distinct())
        qs = User.objects.filter(id__in=user_ids, last_login__lt=cutoff)
        count = 0
        for user in qs:
            if dry_run:
                count += 1
                continue
            Token.objects.filter(user=user).delete()
            count += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Would expire {count} token(s) (users inactive > {days} days)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Expired {count} token(s) (users inactive > {days} days)."))
</think>
