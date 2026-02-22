from django.urls import path

from apps.cases.views import (
    ComplaintCadetReviewAPIView,
    ComplaintResubmitAPIView,
    ComplaintSubmitAPIView,
    SceneCaseCreateAPIView,
)

urlpatterns = [
    path("scene-cases/", SceneCaseCreateAPIView.as_view(), name="cases-scene-case-create"),
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
]

