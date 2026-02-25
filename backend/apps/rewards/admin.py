from django.contrib import admin
from apps.rewards.models import RewardComputationSnapshot


@admin.register(RewardComputationSnapshot)
class RewardComputationSnapshotAdmin(admin.ModelAdmin):
    list_display = ["id", "national_id", "full_name", "max_days_lj", "max_crime_level_di", "ranking_score", "reward_amount_rials", "computed_at"]
    list_filter = ["computed_at"]

