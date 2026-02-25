from django.contrib import admin
from apps.rewards.models import RewardComputationSnapshot, RewardTip


@admin.register(RewardComputationSnapshot)
class RewardComputationSnapshotAdmin(admin.ModelAdmin):
    list_display = ["id", "national_id", "full_name", "max_days_lj", "max_crime_level_di", "ranking_score", "reward_amount_rials", "computed_at"]
    list_filter = ["computed_at"]


@admin.register(RewardTip)
class RewardTipAdmin(admin.ModelAdmin):
    list_display = ["id", "submitted_by", "case_reference", "status", "reward_claim_id", "created_at"]
    list_filter = ["status"]

