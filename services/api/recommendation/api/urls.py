from django.urls import path

from recommendation.api.views import (
    RecommendationApprovalAPIView,
    RecommendationDetailAPIView,
    RecommendationGenerationAPIView,
    RecommendationOperationApprovalAPIView,
    RecommendationOperationRejectionAPIView,
    RecommendationRejectionAPIView,
)

urlpatterns = [
    path(
        "recommendations/workouts/<uuid:workout_id>/generate/",
        RecommendationGenerationAPIView.as_view(),
        name="recommendation-generate",
    ),
    path(
        "recommendations/<uuid:recommendation_id>/",
        RecommendationDetailAPIView.as_view(),
        name="recommendation-detail",
    ),
    path(
        "recommendations/<uuid:recommendation_id>/approve/",
        RecommendationApprovalAPIView.as_view(),
        name="recommendation-approve",
    ),
    path(
        "recommendations/<uuid:recommendation_id>/reject/",
        RecommendationRejectionAPIView.as_view(),
        name="recommendation-reject",
    ),
    path(
        "recommendations/<uuid:recommendation_id>/operations/<uuid:operation_id>/approve/",
        RecommendationOperationApprovalAPIView.as_view(),
        name="recommendation-operation-approve",
    ),
    path(
        "recommendations/<uuid:recommendation_id>/operations/<uuid:operation_id>/reject/",
        RecommendationOperationRejectionAPIView.as_view(),
        name="recommendation-operation-reject",
    ),
]
