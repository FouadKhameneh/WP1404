from django.urls import path

from apps.investigation.views import (
    ReasoningApprovalCreateAPIView,
    ReasoningSubmissionDetailAPIView,
    ReasoningSubmissionListCreateAPIView,
    SuspectAssessmentDetailAPIView,
    SuspectAssessmentListCreateAPIView,
    SuspectAssessmentScoreCreateAPIView,
)

urlpatterns = [
    path("reasonings/", ReasoningSubmissionListCreateAPIView.as_view(), name="investigation-reasoning-list-create"),
    path(
        "reasonings/<int:reasoning_id>/",
        ReasoningSubmissionDetailAPIView.as_view(),
        name="investigation-reasoning-detail",
    ),
    path(
        "reasonings/<int:reasoning_id>/approve/",
        ReasoningApprovalCreateAPIView.as_view(),
        name="investigation-reasoning-approve",
    ),
    path(
        "assessments/",
        SuspectAssessmentListCreateAPIView.as_view(),
        name="investigation-suspect-assessment-list-create",
    ),
    path(
        "assessments/<int:assessment_id>/",
        SuspectAssessmentDetailAPIView.as_view(),
        name="investigation-suspect-assessment-detail",
    ),
    path(
        "assessments/<int:assessment_id>/scores/",
        SuspectAssessmentScoreCreateAPIView.as_view(),
        name="investigation-suspect-assessment-score-create",
    ),
]

