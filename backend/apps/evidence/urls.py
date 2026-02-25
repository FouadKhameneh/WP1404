from django.urls import path

from apps.evidence.views import (
    BiologicalEvidenceCoronerDecisionAPIView,
    BiologicalEvidenceReviewListAPIView,
)

urlpatterns = [
    path(
        "biological/<int:evidence_id>/reviews/",
        BiologicalEvidenceReviewListAPIView.as_view(),
        name="evidence-biological-reviews-list",
    ),
    path(
        "biological/<int:evidence_id>/coroner-decision/",
        BiologicalEvidenceCoronerDecisionAPIView.as_view(),
        name="evidence-biological-coroner-decision",
    ),
]

