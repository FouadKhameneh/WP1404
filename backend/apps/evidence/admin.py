from django.contrib import admin

from .models import Evidence


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "evidence_type", "case", "registrar", "registered_at")
    list_filter = ("evidence_type", "registered_at")
    search_fields = ("title", "description")
    raw_id_fields = ("registrar", "case")
    date_hierarchy = "registered_at"
