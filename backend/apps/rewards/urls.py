from django.urls import path

from apps.rewards.views import RewardClaimVerifyAPIView, RewardTipListCreateAPIView, RewardTipReviewAPIView

urlpatterns = [
    path("tips/", RewardTipListCreateAPIView.as_view(), name="rewards-tip-list-create"),
    path("tips/<int:tip_id>/review/", RewardTipReviewAPIView.as_view(), name="rewards-tip-review"),
    path("verify-claim/", RewardClaimVerifyAPIView.as_view(), name="rewards-claim-verify"),
]
