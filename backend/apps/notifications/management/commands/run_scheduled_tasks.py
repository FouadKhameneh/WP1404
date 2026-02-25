"""Run all scheduled tasks (notifications, most-wanted promotion, token expiry, payment reconciliation)."""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run all scheduler tasks: notifications, wanted_promote, expire_tokens, payment_reconcile."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Pass --dry-run to expire_tokens and payment_reconcile.")

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        extra = ["--dry-run"] if dry_run else []

        self.stdout.write("Running process_notifications...")
        call_command("process_notifications")

        self.stdout.write("Running wanted_promote...")
        call_command("wanted_promote")

        self.stdout.write("Running expire_tokens...")
        call_command("expire_tokens", *extra)

        self.stdout.write("Running payment_reconcile...")
        call_command("payment_reconcile", *extra)

        self.stdout.write(self.style.SUCCESS("All scheduled tasks completed."))
