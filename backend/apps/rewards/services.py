"""
Ranking and reward formula: max(Lj) * max(Di) for ranking; * 20,000,000 for reward amount (rials).
Persist computation snapshots.
Reward tip workflow: base user submit -> police officer review -> detective final review -> unique claim ID.
"""
from datetime import timedelta

from django.utils import timezone

from apps.access.services import user_has_any_role_key
from apps.cases.models import Case
from apps.rewards.models import RewardComputationSnapshot, RewardTip, generate_reward_claim_id
from apps.wanted.models import Wanted

REWARD_MULTIPLIER_RIALS = 20_000_000


def level_to_di(level: str) -> int:
    """Map case level to Di (1-4): Level 3 -> 1, Level 2 -> 2, Level 1 -> 3, Critical -> 4."""
    mapping = {
        Case.Level.LEVEL_3: 1,
        Case.Level.LEVEL_2: 2,
        Case.Level.LEVEL_1: 3,
        Case.Level.CRITICAL: 4,
    }
    return mapping.get(level, 0)


def days_under_surveillance(wanted: Wanted) -> int:
    """Lj: days under surveillance for this (case, participant). End = now or case.closed_at if closed."""
    case = wanted.case
    end = case.closed_at if case.closed_at else timezone.now()
    if end <= wanted.marked_at:
        return 0
    return max(0, (end - wanted.marked_at).days)


def compute_ranking_and_reward_for_person(wanted_entries):
    """Given a list of Wanted entries for one person, compute max(Lj), max(Di), ranking, reward. Returns dict."""
    if not wanted_entries:
        return None
    lj_values = [days_under_surveillance(w) for w in wanted_entries]
    di_values = [level_to_di(w.case.level) for w in wanted_entries]
    max_lj = max(lj_values)
    max_di = max(di_values)
    ranking_score = max_lj * max_di
    reward_amount_rials = ranking_score * REWARD_MULTIPLIER_RIALS
    participant = wanted_entries[0].participant
    return {
        "national_id": participant.national_id or "",
        "full_name": participant.full_name or "",
        "max_days_lj": max_lj,
        "max_crime_level_di": max_di,
        "ranking_score": ranking_score,
        "reward_amount_rials": reward_amount_rials,
    }


def compute_and_persist_snapshots():
    """
    Compute ranking/reward for all persons in Wanted (by national_id), persist snapshots.
    Returns list of created snapshots.
    """
    # All wanted entries with participant and case
    qs = Wanted.objects.select_related("participant", "case").order_by("participant__national_id")
    by_national_id = {}
    for w in qs:
        nid = (w.participant.national_id or "").strip() or f"_participant_{w.participant_id}"
        by_national_id.setdefault(nid, []).append(w)
    created = []
    for nid, entries in by_national_id.items():
        data = compute_ranking_and_reward_for_person(entries)
        if not data:
            continue
        snapshot = RewardComputationSnapshot.objects.create(
            national_id=data["national_id"] or nid,
            full_name=data["full_name"],
            max_days_lj=data["max_days_lj"],
            max_crime_level_di=data["max_crime_level_di"],
            ranking_score=data["ranking_score"],
            reward_amount_rials=data["reward_amount_rials"],
        )
        created.append(snapshot)
    return created


def can_submit_tip(user):
    """Any authenticated user (base user) can submit a tip."""
    return True, None


def can_review_tip_as_officer(user):
    """Only police officer (or patrol_officer) can do first review."""
    if user_has_any_role_key(user, {"police_officer", "patrol_officer", "officer"}):
        return True, None
    return False, "Only police officer can perform first review."


def can_review_tip_as_detective(user):
    """Only detective can do final review."""
    if user_has_any_role_key(user, {"detective"}):
        return True, None
    return False, "Only detective can perform final review."


# Authorized police ranks for reward claim verification (National ID + Unique ID)
CLAIM_VERIFICATION_ROLE_KEYS = {"police_officer", "patrol_officer", "officer", "detective", "sergeant", "captain", "chief"}


def can_verify_reward_claim(user):
    """Only authorized police ranks can verify reward claims."""
    if user_has_any_role_key(user, CLAIM_VERIFICATION_ROLE_KEYS):
        return True, None
    return False, "Only authorized police ranks can verify reward claims."
