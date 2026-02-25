from django.urls import path

from apps.judiciary.views import CaseVerdictAPIView, ReferralPackageAPIView

urlpatterns = [
    path(
        "referral-package/<int:case_id>/",
        ReferralPackageAPIView.as_view(),
        name="judiciary-referral-package",
    ),
    path(
        "cases/<int:case_id>/verdict/",
        CaseVerdictAPIView.as_view(),
        name="judiciary-case-verdict",
    ),
]
