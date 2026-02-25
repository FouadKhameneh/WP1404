from django.contrib import admin

from .models import Evidence, WitnessTestimony, WitnessTestimonyAttachment


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
