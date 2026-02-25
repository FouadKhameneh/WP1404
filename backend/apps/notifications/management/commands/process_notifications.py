"""Scheduled task: process notification queue (placeholder for async notifications)."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Process pending notifications (scheduler task)."

    def handle(self, *args, **options):
        # Placeholder: extend to send emails/push from a queue when notification queue is implemented
        count = 0
        self.stdout.write(self.style.SUCCESS(f"Processed {count} notifications."))
