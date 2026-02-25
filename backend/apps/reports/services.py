"""Aggregated statistics for homepage and general reporting."""
from django.db.models import Count

from apps.cases.models import Case
from apps.investigation.models import ReasoningSubmission
from apps.rewards.models import RewardTip
from apps.wanted.models import Wanted


def get_case_counts():
    """Total cases and by status."""
    total = Case.objects.count()
    by_status = dict(
        Case.objects.values("status").annotate(count=Count("id")).values_list("status", "count")
    )
    return {"total": total, "by_status": by_status}


def get_case_stage_distribution():
    """Count per stage (status) for distribution charts."""
    return list(
        Case.objects.values("status").annotate(count=Count("id")).order_by("-count")
    )


def get_approval_stats():
    """Reasoning approvals: approved vs rejected counts."""
    approved = ReasoningSubmission.objects.filter(status="approved").count()
    rejected = ReasoningSubmission.objects.filter(status="rejected").count()
    pending = ReasoningSubmission.objects.filter(status="pending").count()
    return {"reasoning_approved": approved, "reasoning_rejected": rejected, "reasoning_pending": pending}


def get_wanted_rankings(limit=50):
    """Wanted / most wanted counts and top by ranking (from RewardComputationSnapshot if available)."""
    from apps.rewards.models import RewardComputationSnapshot
    wanted_count = Wanted.objects.filter(status="wanted").count()
    most_wanted_count = Wanted.objects.filter(status="most_wanted").count()
    # Latest snapshot per national_id for ranking
    snapshots = (
        RewardComputationSnapshot.objects.values("national_id", "full_name", "ranking_score", "reward_amount_rials")
        .order_by("-ranking_score")[:limit]
    )
    return {
        "wanted_count": wanted_count,
        "most_wanted_count": most_wanted_count,
        "top_ranked": list(snapshots),
    }


def get_reward_outcomes():
    """Reward tip outcomes: approved, rejected, pending."""
    approved = RewardTip.objects.filter(status="approved").count()
    rejected = RewardTip.objects.filter(status="rejected").count()
    pending = RewardTip.objects.filter(
        status__in=[RewardTip.Status.PENDING_POLICE, RewardTip.Status.PENDING_DETECTIVE]
    ).count()
    return {"tips_approved": approved, "tips_rejected": rejected, "tips_pending": pending}


def get_homepage_stats():
    """Aggregated stats for homepage: case counts, active cases, staff count placeholder, etc."""
    case_counts = get_case_counts()
    active = Case.objects.exclude(
        status__in=[Case.Status.CLOSED, Case.Status.FINAL_INVALID]
    ).count()
    closed = Case.objects.filter(status=Case.Status.CLOSED).count()
    from django.contrib.auth import get_user_model()
    staff_count = get_user_model().objects.filter(is_active=True).count()
    return {
        "total_cases": case_counts["total"],
        "active_cases": active,
        "closed_cases": closed,
        "staff_count": staff_count,
        "by_status": case_counts["by_status"],
    }
