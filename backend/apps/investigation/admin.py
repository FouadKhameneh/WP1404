from django.contrib import admin
from apps.investigation.models import (
    ArrestOrder,
    InterrogationOrder,
    ReasoningApproval,
    ReasoningSubmission,
    SuspectAssessment,
    SuspectAssessmentScoreEntry,
)


@admin.register(ReasoningSubmission)
class ReasoningSubmissionAdmin(admin.ModelAdmin):
    list_display = ["id", "case_reference", "title", "status", "submitted_by", "created_at"]
    list_filter = ["status"]


@admin.register(ReasoningApproval)
class ReasoningApprovalAdmin(admin.ModelAdmin):
    list_display = ["id", "reasoning", "decision", "decided_by", "decided_at"]


class SuspectAssessmentScoreEntryInline(admin.TabularInline):
    model = SuspectAssessmentScoreEntry
    extra = 0
    readonly_fields = ["scored_by", "role_key", "score", "created_at"]
    can_delete = False  # immutable history

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SuspectAssessment)
class SuspectAssessmentAdmin(admin.ModelAdmin):
    list_display = ["id", "case", "participant", "created_at"]
    inlines = [SuspectAssessmentScoreEntryInline]


@admin.register(ArrestOrder)
class ArrestOrderAdmin(admin.ModelAdmin):
    list_display = ["id", "case", "participant", "issued_by", "status", "issued_at"]
    list_filter = ["status"]


@admin.register(InterrogationOrder)
class InterrogationOrderAdmin(admin.ModelAdmin):
    list_display = ["id", "case", "participant", "ordered_by", "status", "ordered_at", "scheduled_at"]
    list_filter = ["status"]

