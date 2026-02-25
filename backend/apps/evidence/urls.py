from django.urls import path

from apps.evidence.views import (
    BiologicalEvidenceCoronerDecisionAPIView,
    BiologicalEvidenceReviewListAPIView,
    EvidenceLinkDetailAPIView,
    EvidenceLinkListCreateAPIView,
    EvidenceMediaAccessByTokenAPIView,
    EvidenceMediaSignedURLApiView,
    EvidenceMediaStreamAPIView,
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
    path(
        "media/<str:media_type>/<int:media_id>/",
        EvidenceMediaStreamAPIView.as_view(),
        name="evidence-media-stream",
    ),
    path(
        "media/signed-url/",
        EvidenceMediaSignedURLApiView.as_view(),
        name="evidence-media-signed-url",
    ),
    path(
        "media/access/",
        EvidenceMediaAccessByTokenAPIView.as_view(),
        name="evidence-media-access-by-token",
    ),
    path("links/", EvidenceLinkListCreateAPIView.as_view(), name="evidence-links-list-create"),
    path("links/<int:link_id>/", EvidenceLinkDetailAPIView.as_view(), name="evidence-links-detail"),
]

