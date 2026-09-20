from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.views import health, ready

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("ready/", ready),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("datahub.urls")),
    path("api/v1/sources/", include("sources.urls")),
    path("api/v1/scrapers/", include("scraping.urls")),
    path("api/v1/exports/", include("exports.urls")),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
]
