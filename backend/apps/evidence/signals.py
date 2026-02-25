"""
Evidence signals for metadata persistence and storage lifecycle.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.evidence.models import BiologicalMedicalMediaReference, WitnessTestimonyAttachment
from apps.evidence.services.media import persist_attachment_metadata


@receiver(post_save, sender=WitnessTestimonyAttachment)
def witness_attachment_metadata(sender, instance, created, **kwargs):
    if instance.file and instance.file.name:
        persist_attachment_metadata(instance)


@receiver(post_save, sender=BiologicalMedicalMediaReference)
def biological_media_metadata(sender, instance, created, **kwargs):
    if instance.file and instance.file.name:
        persist_attachment_metadata(instance)
