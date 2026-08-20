from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from recommendation.api.serializers import RecommendationSerializer
from recommendation.services import (
    RecommendationConflict,
    RecommendationNotFound,
    accept_operation,
    accept_recommendation,
    get_recommendation,
    reject_operation,
    reject_recommendation,
)


class RecommendationDetailAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RecommendationSerializer

    @extend_schema(
        tags=["Recommendation"],
        operation_id="recommendation_retrieve",
        responses={200: RecommendationSerializer},
    )
    def get(self, request: Request, id: str) -> Response:
        recommendation = get_recommendation(request.user, str(id))
        if recommendation is None:
            raise NotFound()
        return Response(RecommendationSerializer(recommendation).data)


class RecommendationActionAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        tags=["Recommendation"],
        operation_id="recommendation_action",
        request=None,
        responses={200: RecommendationSerializer},
    )
    def post(self, request: Request, id: str, action: str) -> Response:
        if action not in {"accept", "reject"}:
            raise NotFound()
        try:
            handler = (
                accept_recommendation if action == "accept" else reject_recommendation
            )
            recommendation = handler(user=request.user, recommendation_id=str(id))
        except RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except RecommendationConflict as exc:
            raise ValidationError(str(exc)) from exc
        return Response(RecommendationSerializer(recommendation).data)


class RecommendationOperationAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        tags=["Recommendation"],
        operation_id="recommendation_operation_action",
        request=None,
        responses={200: RecommendationSerializer},
    )
    def post(
        self, request: Request, id: str, operation_id: str, action: str
    ) -> Response:
        if action not in {"accept", "reject"}:
            raise NotFound()
        try:
            handler = accept_operation if action == "accept" else reject_operation
            recommendation = handler(
                user=request.user,
                recommendation_id=str(id),
                operation_id=str(operation_id),
            )
        except RecommendationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except RecommendationConflict as exc:
            raise ValidationError(str(exc)) from exc
        return Response(RecommendationSerializer(recommendation).data)


"""     
    disable the operation update as coach displays recommendaitons and 
    do not wanna get mismatch between recommendaiton and the coach message 

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
"""
