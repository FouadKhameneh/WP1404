from django.urls import path

from apps.reports.views import (
    ApprovalsStatsAPIView,
    CaseCountsAPIView,
    GeneralReportAPIView,
    HomepageStatsAPIView,
    RewardOutcomesAPIView,
    WantedRankingsAPIView,
)

urlpatterns = [
    path("homepage/", HomepageStatsAPIView.as_view(), name="reports-homepage"),
    path("cases/", CaseCountsAPIView.as_view(), name="reports-case-counts"),
    path("approvals/", ApprovalsStatsAPIView.as_view(), name="reports-approvals"),
    path("wanted-rankings/", WantedRankingsAPIView.as_view(), name="reports-wanted-rankings"),
    path("reward-outcomes/", RewardOutcomesAPIView.as_view(), name="reports-reward-outcomes"),
    path("general/", GeneralReportAPIView.as_view(), name="reports-general"),
]
