from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.cases.models import CaseParticipant
from apps.wanted.models import Wanted


@receiver(post_save, sender=CaseParticipant)
def on_suspect_marked(sender, instance, created, **kwargs):
    """On suspect mark -> Wanted: create Wanted entry when a suspect is added to a case."""
    if not created:
        return
    if instance.role_in_case != CaseParticipant.RoleInCase.SUSPECT:
        return
    Wanted.objects.get_or_create(
        case=instance.case,
        participant=instance,
        defaults={"status": Wanted.Status.WANTED},
    )
