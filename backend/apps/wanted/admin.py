from django.contrib import admin
from apps.wanted.models import Wanted


@admin.register(Wanted)
class WantedAdmin(admin.ModelAdmin):
    list_display = ["id", "case", "participant", "status", "marked_at", "promoted_at"]
    list_filter = ["status"]

