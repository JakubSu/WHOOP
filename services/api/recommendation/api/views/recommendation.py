from rest_framework import permissions, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.infrastructure.exceptions import AIInfrastructureError
from recommendation import services
from recommendation.api.serializers import ApproveRecommendationSerializer


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict."
    default_code = "conflict"


class RecommendationGenerationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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

    def get(self, request: Request, recommendation_id: str) -> Response:
        recommendation = services.get_recommendation(str(request.user.id), str(recommendation_id))
        if recommendation is None:
            raise NotFound()
        return Response(services.serialize_recommendation(recommendation))


class RecommendationApprovalAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, recommendation_id: str) -> Response:
        raise ValidationError({"detail": "Use operation-level approval."})


class RecommendationOperationApprovalAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, recommendation_id: str, operation_id: str) -> Response:
        serializer = ApproveRecommendationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            recommendation = services.approve_recommendation_operation(
                str(request.user.id),
                str(recommendation_id),
                str(operation_id),
                expected_workout_version=serializer.validated_data.get("expected_workout_version"),
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

    def post(self, request: Request, recommendation_id: str) -> Response:
        raise ValidationError({"detail": "Use operation-level rejection."})


class RecommendationOperationRejectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, recommendation_id: str, operation_id: str) -> Response:
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
