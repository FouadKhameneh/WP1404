from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/identity/", include("apps.identity.urls")),
    path("api/v1/access/", include("apps.access.urls")),
    path("api/v1/cases/", include("apps.cases.urls")),
    path("api/v1/evidence/", include("apps.evidence.urls")),
    path("api/v1/investigation/", include("apps.investigation.urls")),
    path("api/v1/judiciary/", include("apps.judiciary.urls")),
    path("api/v1/wanted/", include("apps.wanted.urls")),
    path("api/v1/rewards/", include("apps.rewards.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
