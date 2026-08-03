from django.urls import path

from recommendation.api.views import (
    RecommendationActionAPIView,
    RecommendationDetailAPIView,
    RecommendationOperationAPIView,
)

urlpatterns = [
    path(
        "recommendations/<uuid:id>/",
        RecommendationDetailAPIView.as_view(),
        name="recommendation-detail",
    ),
    path(
        "recommendations/<uuid:id>/<str:action>/",
        RecommendationActionAPIView.as_view(),
        name="recommendation-action",
    ),
    path(
        "recommendations/<uuid:id>/operations/<uuid:operation_id>/",
        RecommendationOperationAPIView.as_view(),
        name="recommendation-operation",
    ),
    path(
        "recommendations/<uuid:id>/operations/<uuid:operation_id>/<str:action>/",
        RecommendationOperationAPIView.as_view(),
        name="recommendation-operation-action",
    ),
]
