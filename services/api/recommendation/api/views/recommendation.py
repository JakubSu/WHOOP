from typing import Any, cast

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from recommendation import services
from recommendation.api.serializers import (
    AcceptRecommendationSerializer,
    RecommendationErrorDetailSerializer,
    RecommendationSerializer,
    RecommendationUpdateSerializer,
)


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict."
    default_code = "conflict"


class RecommendationCollectionAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RecommendationSerializer

    @extend_schema(
        tags=["Recommendations"],
        summary="List recommendations",
        description="Returns recommendations visible to the authenticated user.",
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter recommendations by status.",
            )
        ],
        responses={200: RecommendationSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        recommendations = services.list_recommendations(
            str(request.user.id),
            status=request.query_params.get("status"),
        )
        return Response(
            [
                services.serialize_recommendation(recommendation)
                for recommendation in recommendations
            ]
        )


class RecommendationDetailAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RecommendationSerializer

    @extend_schema(
        tags=["Recommendations"],
        summary="Get recommendation",
        description="Returns a single recommendation.",
        responses={
            200: RecommendationSerializer,
            404: OpenApiResponse(
                response=RecommendationErrorDetailSerializer,
                description="Recommendation not found.",
            ),
        },
    )
    def get(self, request: Request, id: str) -> Response:
        recommendation = services.get_recommendation(str(request.user.id), str(id))
        if recommendation is None:
            raise NotFound()
        return Response(services.serialize_recommendation(recommendation))

    @extend_schema(
        tags=["Recommendations"],
        summary="Update recommendation partially",
        description="Updates recommendation review status.",
        request=RecommendationUpdateSerializer,
        responses={
            200: RecommendationSerializer,
            400: OpenApiResponse(
                response=RecommendationErrorDetailSerializer,
                description="Validation error.",
            ),
            404: OpenApiResponse(
                response=RecommendationErrorDetailSerializer,
                description="Recommendation not found.",
            ),
            409: OpenApiResponse(
                response=RecommendationErrorDetailSerializer,
                description="Recommendation is no longer pending.",
            ),
        },
    )
    def patch(self, request: Request, id: str) -> Response:
        serializer = RecommendationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)
        status_value = validated_data.get("status")
        if not status_value:
            raise ValidationError({"detail": "status is required."})
        try:
            recommendation = services.update_recommendation_status(
                str(request.user.id),
                str(id),
                status=str(status_value),
            )
        except services.RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.RecommendationConflict as exc:
            raise Conflict(str(exc)) from exc
        except services.RecommendationValidationError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(services.serialize_recommendation(recommendation))


class RecommendationAcceptAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AcceptRecommendationSerializer

    @extend_schema(
        tags=["Recommendations"],
        summary="Accept recommendation",
        description="Accepts a pending recommendation and applies its operation.",
        request=AcceptRecommendationSerializer,
        responses={
            200: RecommendationSerializer,
            400: OpenApiResponse(
                response=RecommendationErrorDetailSerializer,
                description="Validation error.",
            ),
            404: OpenApiResponse(
                response=RecommendationErrorDetailSerializer,
                description="Recommendation not found.",
            ),
            409: OpenApiResponse(
                response=RecommendationErrorDetailSerializer,
                description="Recommendation is no longer pending or the workout version conflicts.",
            ),
        },
    )
    def post(self, request: Request, id: str) -> Response:
        serializer = AcceptRecommendationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)
        try:
            recommendation = services.accept_recommendation(
                str(request.user.id),
                str(id),
                expected_workout_version=validated_data.get("expected_workout_version"),
            )
        except services.RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.RecommendationConflict as exc:
            raise Conflict(str(exc)) from exc
        except services.RecommendationValidationError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(services.serialize_recommendation(recommendation))


class RecommendationRejectAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RecommendationSerializer

    @extend_schema(
        tags=["Recommendations"],
        summary="Reject recommendation",
        description="Rejects a pending recommendation.",
        request=None,
        responses={
            200: RecommendationSerializer,
            404: OpenApiResponse(
                response=RecommendationErrorDetailSerializer,
                description="Recommendation not found.",
            ),
            409: OpenApiResponse(
                response=RecommendationErrorDetailSerializer,
                description="Recommendation is no longer pending.",
            ),
        },
    )
    def post(self, request: Request, id: str) -> Response:
        try:
            recommendation = services.reject_recommendation(
                str(request.user.id), str(id)
            )
        except services.RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.RecommendationConflict as exc:
            raise Conflict(str(exc)) from exc
        return Response(services.serialize_recommendation(recommendation))
