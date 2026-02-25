from django.urls import path

from apps.investigation.views import (
    ReasoningApprovalCreateAPIView,
    ReasoningSubmissionDetailAPIView,
    ReasoningSubmissionListCreateAPIView,
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
]

