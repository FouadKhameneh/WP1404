from django.urls import path

from apps.cases.views import (
    CaseDetailAPIView,
    CaseListAPIView,
    CaseStatusTransitionAPIView,
    CaseSuspectAddAPIView,
    ComplaintCadetReviewAPIView,
    ComplaintResubmitAPIView,
    ComplaintSubmitAPIView,
    SceneCaseApproveAPIView,
    SceneCaseCreateAPIView,
)

urlpatterns = [
    path("cases/", CaseListAPIView.as_view(), name="cases-list"),
    path("cases/<int:case_id>/", CaseDetailAPIView.as_view(), name="cases-detail"),
    path("scene-cases/", SceneCaseCreateAPIView.as_view(), name="cases-scene-case-create"),
    path(
        "scene-cases/<int:case_id>/approve/",
        SceneCaseApproveAPIView.as_view(),
        name="cases-scene-case-approve",
    ),
    path("complaints/", ComplaintSubmitAPIView.as_view(), name="cases-complaint-submit"),
    path(
        "complaints/<int:complaint_id>/review/",
        ComplaintCadetReviewAPIView.as_view(),
        name="cases-complaint-review",
    ),
    path(
        "complaints/<int:complaint_id>/resubmit/",
        ComplaintResubmitAPIView.as_view(),
        name="cases-complaint-resubmit",
    ),
    path(
        "cases/<int:case_id>/suspects/",
        CaseSuspectAddAPIView.as_view(),
        name="cases-suspect-add",
    ),
    path(
        "cases/<int:case_id>/transition-status/",
        CaseStatusTransitionAPIView.as_view(),
        name="cases-status-transition",
    ),
]

