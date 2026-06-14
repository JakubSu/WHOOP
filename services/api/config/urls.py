from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(
            authentication_classes=[],
            permission_classes=[AllowAny],
        ),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            authentication_classes=[],
            permission_classes=[AllowAny],
        ),
        name="swagger-ui",
    ),
    path("api/v1/", include("users.api.urls")),
    path("api/v1/", include("training.api.urls")),
    path("api/v1/", include("recommendation.api.urls")),
    path("api/v1/", include("whoop.api.urls")),
]
