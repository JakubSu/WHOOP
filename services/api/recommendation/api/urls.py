from django.urls import path

from recommendation.api.views import (
    RecommendationAcceptAPIView,
    RecommendationCollectionAPIView,
    RecommendationDetailAPIView,
    RecommendationRejectAPIView,
)

urlpatterns = [
    path(
        "recommendations/",
        RecommendationCollectionAPIView.as_view(),
        name="recommendation-collection",
    ),
    path(
        "recommendations/<uuid:id>/",
        RecommendationDetailAPIView.as_view(),
        name="recommendation-detail",
    ),
    path(
        "recommendations/<uuid:id>/accept/",
        RecommendationAcceptAPIView.as_view(),
        name="recommendation-accept",
    ),
    path(
        "recommendations/<uuid:id>/reject/",
        RecommendationRejectAPIView.as_view(),
        name="recommendation-reject",
    ),
]
