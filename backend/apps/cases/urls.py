from django.urls import path

from apps.cases.views import ComplaintCadetReviewAPIView, ComplaintResubmitAPIView, ComplaintSubmitAPIView

urlpatterns = [
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

