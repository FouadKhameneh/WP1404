from django.contrib import admin
from apps.judiciary.models import CaseVerdict


@admin.register(CaseVerdict)
class CaseVerdictAdmin(admin.ModelAdmin):
    list_display = ["id", "case", "judge", "verdict", "punishment_title", "recorded_at"]
    list_filter = ["verdict"]

