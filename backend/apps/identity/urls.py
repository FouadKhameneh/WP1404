from django.urls import path

from apps.identity.views import CurrentUserAPIView, LoginAPIView, LogoutAPIView, RegisterAPIView

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="identity-auth-register"),
    path("auth/login/", LoginAPIView.as_view(), name="identity-auth-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="identity-auth-logout"),
    path("auth/me/", CurrentUserAPIView.as_view(), name="identity-auth-me"),
]

