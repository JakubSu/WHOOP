from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("users.api.urls")),
    path("api/v1/", include("training.api.urls")),
    path("api/v1/", include("recommendation.api.urls")),
    path("api/v1/", include("whoop.api.urls")),
]
