from typing import Any, cast

from rest_framework import permissions
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from recommendation import services
from recommendation.api.serializers import RecommendationSerializer


class RecommendationDetailAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RecommendationSerializer

    def get(self, request: Request, id: str) -> Response:
        recommendation = services.get_recommendation(request.user, str(id))
        if recommendation is None:
            raise NotFound()
        return Response(services.serialize_recommendation(recommendation))


class RecommendationActionAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request: Request, id: str, action: str) -> Response:
        if action not in {"accept", "reject"}:
            raise NotFound()
        try:
            handler = (
                services.accept_recommendation
                if action == "accept"
                else services.reject_recommendation
            )
            recommendation = handler(user=request.user, recommendation_id=str(id))
        except services.RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.RecommendationConflict as exc:
            raise ValidationError(str(exc)) from exc
        return Response(services.serialize_recommendation(recommendation))


class RecommendationOperationAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(
        self, request: Request, id: str, operation_id: str, action: str
    ) -> Response:
        if action not in {"accept", "reject"}:
            raise NotFound()
        try:
            handler = (
                services.accept_operation
                if action == "accept"
                else services.reject_operation
            )
            recommendation = handler(
                user=request.user,
                recommendation_id=str(id),
                operation_id=str(operation_id),
            )
        except services.RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.RecommendationConflict as exc:
            raise ValidationError(str(exc)) from exc
        return Response(services.serialize_recommendation(recommendation))

    def patch(self, request: Request, id: str, operation_id: str) -> Response:
        try:
            recommendation = services.revise_operation(
                user=request.user,
                recommendation_id=str(id),
                operation_id=str(operation_id),
                replacement=cast(dict[str, Any], request.data),
            )
        except services.RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except (
            services.RecommendationConflict,
            services.RecommendationValidationError,
        ) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(services.serialize_recommendation(recommendation))
