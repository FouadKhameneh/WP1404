from django.core.management.base import BaseCommand

from apps.wanted.services import promote_to_most_wanted


class Command(BaseCommand):
    help = "Promote Wanted to Most Wanted when marked more than one month ago (for scheduler)."

    def handle(self, *args, **options):
        count = promote_to_most_wanted()
        self.stdout.write(self.style.SUCCESS(f"Promoted {count} wanted entries to most_wanted."))
