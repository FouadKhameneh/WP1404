from django.urls import path

from apps.wanted.views import WantedListAPIView

urlpatterns = [
    path("", WantedListAPIView.as_view(), name="wanted-list"),
]
