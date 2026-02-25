"""
Evidence signals for metadata persistence, storage lifecycle, and notification events.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.evidence.models import BiologicalMedicalMediaReference, Evidence, WitnessTestimonyAttachment
from apps.evidence.services.media import persist_attachment_metadata
from apps.notifications.services import log_timeline_event


@receiver(post_save, sender=Evidence)
def evidence_registered_notification(sender, instance, created, **kwargs):
    """Notify relevant roles when new evidence is registered (visible in case timeline)."""
    if not created:
        return
    case_reference = ""
    if instance.case_id:
        try:
            case_reference = instance.case.case_number
        except Exception:
            pass
    evidence_type_display = instance.get_evidence_type_display()
    log_timeline_event(
        event_type="evidence.registered",
        actor=instance.registrar,
        summary=f"New evidence registered: {evidence_type_display} — {instance.title}",
        target_type="evidence.evidence",
        target_id=str(instance.pk),
        case_reference=case_reference,
        payload_summary={
            "evidence_type": instance.evidence_type,
            "title": instance.title,
        },
    )


@receiver(post_save, sender=WitnessTestimonyAttachment)
def witness_attachment_metadata(sender, instance, created, **kwargs):
    if instance.file and instance.file.name:
        persist_attachment_metadata(instance)


@receiver(post_save, sender=BiologicalMedicalMediaReference)
def biological_media_metadata(sender, instance, created, **kwargs):
    if instance.file and instance.file.name:
        persist_attachment_metadata(instance)
