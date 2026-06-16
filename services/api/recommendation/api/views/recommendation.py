from typing import Any, cast

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import permissions, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from ai.infrastructure.exceptions import AIInfrastructureError
import recommendation.services as services
from recommendation.api.serializers import (
    ApproveRecommendationSerializer,
    RecommendationSerializer,
)


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict."
    default_code = "conflict"


ErrorDetailSerializer = inline_serializer(
    name="RecommendationErrorDetail",
    fields={"detail": serializers.CharField()},
)


class RecommendationGenerationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecommendationSerializer

    @extend_schema(
        tags=["Recommendations"],
        summary="Generate workout recommendation",
        description="Generates a workout recommendation for the specified workout and returns the recommendation with operation-level suggestions.",
        request=None,
        responses={
            201: RecommendationSerializer,
            400: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Validation or AI generation error.",
            ),
            404: OpenApiResponse(
                response=ErrorDetailSerializer, description="Workout not found."
            ),
        },
        examples=[
            OpenApiExample(
                "Recommendation response",
                response_only=True,
                value={
                    "id": "11f8dc48-40e3-48e2-9a17-880fa9044db7",
                    "user_id": "user-123",
                    "workout_id": "7ca4d8b5-9c08-4c70-a844-c1ccb4627648",
                    "snapshot_version": "2026-06-15T12:00:00+00:00",
                    "status": "pending",
                    "summary": "Reduce upper body volume after recent WHOOP strain.",
                    "reason": "Recovery is lower than normal.",
                    "operations": [
                        {
                            "id": "a5f95b51-1b92-4388-ae74-3c6134a5161d",
                            "sequence": 1,
                            "operation_type": "replace_exercise",
                            "status": "pending",
                            "payload": {
                                "workout_exercise_id": "1896f241-f7e3-4821-b60b-611bde5c0f0f",
                                "replacement_exercise_id": "a7e65f0e-5d16-4094-a0d4-ee7090c3c577",
                            },
                            "display_text": "Replace Bench Press with Goblet Squat",
                        }
                    ],
                    "created_at": "2026-06-15T12:00:10+00:00",
                    "updated_at": "2026-06-15T12:00:10+00:00",
                },
            ),
        ],
    )
    def post(self, request: Request, workout_id: str) -> Response:
        try:
            recommendation = services.generate_recommendation_for_workout(
                str(request.user.id),
                str(workout_id),
            )
        except services.RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.RecommendationValidationError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        except AIInfrastructureError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(
            services.serialize_recommendation(recommendation),
            status=status.HTTP_201_CREATED,
        )


class RecommendationDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecommendationSerializer

    @extend_schema(
        tags=["Recommendations"],
        summary="Get recommendation",
        description="Returns a single recommendation with all of its proposed operations.",
        responses={
            200: RecommendationSerializer,
            404: OpenApiResponse(
                response=ErrorDetailSerializer, description="Recommendation not found."
            ),
        },
    )
    def get(self, request: Request, recommendation_id: str) -> Response:
        recommendation = services.get_recommendation(
            str(request.user.id), str(recommendation_id)
        )
        if recommendation is None:
            raise NotFound()
        return Response(services.serialize_recommendation(recommendation))


class RecommendationApprovalAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Recommendations"],
        summary="Approve recommendation",
        description="Legacy endpoint kept for compatibility. Operation-level approval must be used instead.",
        request=None,
        responses={
            400: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Always returns a validation error directing clients to operation-level approval.",
            ),
        },
    )
    def post(self, request: Request, recommendation_id: str) -> Response:
        raise ValidationError({"detail": "Use operation-level approval."})


class RecommendationOperationApprovalAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApproveRecommendationSerializer

    @extend_schema(
        tags=["Recommendations"],
        summary="Approve recommendation operation",
        description="Approves a single recommendation operation and returns the updated recommendation aggregate.",
        request=ApproveRecommendationSerializer,
        responses={
            200: RecommendationSerializer,
            400: OpenApiResponse(
                response=ErrorDetailSerializer, description="Validation error."
            ),
            404: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Recommendation or operation not found.",
            ),
            409: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Workout version conflict or operation is no longer pending.",
            ),
        },
        examples=[
            OpenApiExample(
                "Approve operation request",
                request_only=True,
                value={"expected_workout_version": "2026-06-15T12:00:00+00:00"},
            ),
        ],
    )
    def post(
        self, request: Request, recommendation_id: str, operation_id: str
    ) -> Response:
        serializer = ApproveRecommendationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)
        try:
            recommendation = services.approve_recommendation_operation(
                str(request.user.id),
                str(recommendation_id),
                str(operation_id),
                expected_workout_version=validated_data.get("expected_workout_version"),
            )
        except services.RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.RecommendationConflict as exc:
            raise Conflict(str(exc)) from exc
        except services.RecommendationValidationError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(services.serialize_recommendation(recommendation))


class RecommendationRejectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Recommendations"],
        summary="Reject recommendation",
        description="Legacy endpoint kept for compatibility. Operation-level rejection must be used instead.",
        request=None,
        responses={
            400: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Always returns a validation error directing clients to operation-level rejection.",
            ),
        },
    )
    def post(self, request: Request, recommendation_id: str) -> Response:
        raise ValidationError({"detail": "Use operation-level rejection."})


class RecommendationOperationRejectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecommendationSerializer

    @extend_schema(
        tags=["Recommendations"],
        summary="Reject recommendation operation",
        description="Rejects a single recommendation operation and returns the updated recommendation aggregate.",
        request=None,
        responses={
            200: RecommendationSerializer,
            404: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Recommendation or operation not found.",
            ),
            409: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Operation is no longer pending.",
            ),
        },
    )
    def post(
        self, request: Request, recommendation_id: str, operation_id: str
    ) -> Response:
        try:
            recommendation = services.reject_recommendation_operation(
                str(request.user.id),
                str(recommendation_id),
                str(operation_id),
            )
        except services.RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.RecommendationConflict as exc:
            raise Conflict(str(exc)) from exc
        return Response(services.serialize_recommendation(recommendation))
