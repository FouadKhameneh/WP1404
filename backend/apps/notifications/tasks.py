"""Celery tasks for async/scheduled processing."""
from celery import shared_task
from django.core.management import call_command


@shared_task(name="apps.notifications.tasks.run_all_scheduled_tasks")
def run_all_scheduled_tasks():
    """Run all scheduler tasks: notifications, most-wanted promotion, token expiry, payment reconciliation."""
    call_command("process_notifications")
    call_command("wanted_promote")
    call_command("expire_tokens")
    call_command("payment_reconcile")
