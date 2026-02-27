from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.identity.services import success_response
from apps.reports.services import (
    get_approval_stats,
    get_case_counts,
    get_case_stage_distribution,
    get_homepage_stats,
    get_reward_outcomes,
    get_wanted_rankings,
)


class LandingStatsAPIView(APIView):
    """Public stats for landing page: total closed cases, staff count, active cases. No auth required."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        data = get_homepage_stats()
        return success_response({
            "closed_cases": data.get("closed_cases", 0),
            "staff_count": data.get("staff_count", 0),
            "active_cases": data.get("active_cases", 0),
            "total_cases": data.get("total_cases", 0),
        }, status_code=status.HTTP_200_OK)


class HomepageStatsAPIView(APIView):
    """Stats for homepage: case counts, active/closed, staff count."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["reports.view"]}

    def get(self, request):
        data = get_homepage_stats()
        return success_response(data, status_code=status.HTTP_200_OK)


class CaseCountsAPIView(APIView):
    """Case counts and stage distribution."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["reports.view"]}

    def get(self, request):
        data = {
            "counts": get_case_counts(),
            "stage_distribution": get_case_stage_distribution(),
        }
        return success_response(data, status_code=status.HTTP_200_OK)


class ApprovalsStatsAPIView(APIView):
    """Approval statistics (e.g. reasoning approved/rejected/pending)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["reports.view"]}

    def get(self, request):
        data = get_approval_stats()
        return success_response(data, status_code=status.HTTP_200_OK)


class WantedRankingsAPIView(APIView):
    """Wanted/most wanted counts and top ranked list."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["reports.view"]}

    def get(self, request):
        limit = min(int(request.query_params.get("limit", 50)), 100)
        data = get_wanted_rankings(limit=limit)
        return success_response(data, status_code=status.HTTP_200_OK)


class RewardOutcomesAPIView(APIView):
    """Reward tip outcomes: approved, rejected, pending."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["reports.view"]}

    def get(self, request):
        data = get_reward_outcomes()
        return success_response(data, status_code=status.HTTP_200_OK)


class GeneralReportAPIView(APIView):
    """Single endpoint aggregating all report data for general reporting."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["reports.view"]}

    def get(self, request):
        data = {
            "homepage": get_homepage_stats(),
            "case_counts": get_case_counts(),
            "stage_distribution": get_case_stage_distribution(),
            "approvals": get_approval_stats(),
            "wanted_rankings": get_wanted_rankings(limit=20),
            "reward_outcomes": get_reward_outcomes(),
        }
        return success_response(data, status_code=status.HTTP_200_OK)
