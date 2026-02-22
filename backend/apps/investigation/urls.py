from django.urls import path

from apps.investigation.views import ReasoningApprovalCreateAPIView, ReasoningSubmissionListCreateAPIView

urlpatterns = [
    path("reasonings/", ReasoningSubmissionListCreateAPIView.as_view(), name="investigation-reasoning-list-create"),
    path(
        "reasonings/<int:reasoning_id>/approve/",
        ReasoningApprovalCreateAPIView.as_view(),
        name="investigation-reasoning-approve",
    ),
]

