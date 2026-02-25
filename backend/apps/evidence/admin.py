from django.contrib import admin

from .models import (
    BiologicalMedicalEvidence,
    BiologicalMedicalMediaReference,
    Evidence,
    EvidenceReview,
    IdentificationEvidence,
    OtherEvidence,
    VehicleEvidence,
    WitnessTestimony,
    WitnessTestimonyAttachment,
)


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "evidence_type", "case", "registrar", "registered_at")
    list_filter = ("evidence_type", "registered_at")
    search_fields = ("title", "description")
    raw_id_fields = ("registrar", "case")
    date_hierarchy = "registered_at"


class WitnessTestimonyAttachmentInline(admin.TabularInline):
    model = WitnessTestimonyAttachment
    extra = 0
    fields = ("file", "media_type", "duration_seconds", "width", "height", "file_size", "mime_type", "caption")


@admin.register(WitnessTestimony)
class WitnessTestimonyAdmin(admin.ModelAdmin):
    list_display = ("title", "case", "registrar", "registered_at")
    list_filter = ("registered_at",)
    search_fields = ("title", "description", "transcript")
    raw_id_fields = ("registrar", "case")
    date_hierarchy = "registered_at"
    inlines = [WitnessTestimonyAttachmentInline]


class BiologicalMedicalMediaReferenceInline(admin.TabularInline):
    model = BiologicalMedicalMediaReference
    extra = 0
    fields = ("file", "media_type", "width", "height", "file_size", "mime_type", "caption")


@admin.register(BiologicalMedicalEvidence)
class BiologicalMedicalEvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "case", "registrar", "coroner_status", "result_submitted_at", "registered_at")
    list_filter = ("coroner_status", "registered_at")
    search_fields = ("title", "description", "coroner_result")
    raw_id_fields = ("registrar", "case", "coroner")
    date_hierarchy = "registered_at"
    inlines = [BiologicalMedicalMediaReferenceInline, EvidenceReviewInline]


@admin.register(VehicleEvidence)
class VehicleEvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "model", "color", "plate", "serial_number", "case", "registered_at")
    list_filter = ("registered_at",)
    search_fields = ("title", "description", "model", "plate", "serial_number")
    raw_id_fields = ("registrar", "case")
    date_hierarchy = "registered_at"


@admin.register(IdentificationEvidence)
class IdentificationEvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "case", "registrar", "registered_at")
    list_filter = ("registered_at",)
    search_fields = ("title", "description")
    raw_id_fields = ("registrar", "case")
    date_hierarchy = "registered_at"


class EvidenceReviewInline(admin.TabularInline):
    model = EvidenceReview
    extra = 0
    readonly_fields = ("reviewed_by", "reviewed_at")
    fields = ("decision", "follow_up_notes", "reviewed_by", "reviewed_at")


@admin.register(EvidenceReview)
class EvidenceReviewAdmin(admin.ModelAdmin):
    list_display = ("biological_medical_evidence", "decision", "reviewed_by", "reviewed_at")
    list_filter = ("decision", "reviewed_at")
    raw_id_fields = ("biological_medical_evidence", "reviewed_by")
    date_hierarchy = "reviewed_at"


@admin.register(OtherEvidence)
class OtherEvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "case", "registrar", "registered_at")
    list_filter = ("registered_at",)
    search_fields = ("title", "description")
    raw_id_fields = ("registrar", "case")
    date_hierarchy = "registered_at"
