from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from training import services
from training.api.serializers import PlanWorkoutSerializer, TrainingPlanSerializer
from training.api.views.helpers import validated_data_as_dict


class TrainingPlanErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class TrainingPlanCollectionAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TrainingPlanSerializer

    @extend_schema(
        tags=["Training"],
        summary="List training plans",
        description="Returns all training plans owned by the authenticated user.",
        responses={200: TrainingPlanSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        training_plans = services.list_training_plans(str(request.user.id))
        return Response(TrainingPlanSerializer(training_plans, many=True).data)

    @extend_schema(
        tags=["Training"],
        summary="Create training plan",
        description="Creates a new training plan for the authenticated user.",
        request=TrainingPlanSerializer,
        responses={
            201: TrainingPlanSerializer,
            400: OpenApiResponse(
                response=TrainingPlanErrorDetailSerializer,
                description="Validation error.",
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = TrainingPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            training_plan = services.create_training_plan(
                validated_data_as_dict(serializer), user_id=str(request.user.id)
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(
            TrainingPlanSerializer(training_plan).data, status=status.HTTP_201_CREATED
        )


class TrainingPlanDetailAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TrainingPlanSerializer

    @extend_schema(
        tags=["Training"],
        summary="Get training plan",
        description="Returns a single training plan owned by the authenticated user.",
        responses={
            200: TrainingPlanSerializer,
            404: OpenApiResponse(
                response=TrainingPlanErrorDetailSerializer,
                description="Training plan not found.",
            ),
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()
        return Response(TrainingPlanSerializer(training_plan).data)

    @extend_schema(
        tags=["Training"],
        summary="Update training plan partially",
        description="Applies a partial update to a training plan.",
        request=TrainingPlanSerializer,
        responses={
            200: TrainingPlanSerializer,
            400: OpenApiResponse(
                response=TrainingPlanErrorDetailSerializer,
                description="Validation error.",
            ),
            404: OpenApiResponse(
                response=TrainingPlanErrorDetailSerializer,
                description="Training plan not found.",
            ),
        },
    )
    def patch(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()

        serializer = TrainingPlanSerializer(
            training_plan, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_training_plan(
                training_plan, validated_data_as_dict(serializer)
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(TrainingPlanSerializer(updated).data)

    @extend_schema(
        tags=["Training"],
        summary="Replace training plan",
        description="Replaces the training plan with the provided payload.",
        request=TrainingPlanSerializer,
        responses={
            200: TrainingPlanSerializer,
            400: OpenApiResponse(
                response=TrainingPlanErrorDetailSerializer,
                description="Validation error.",
            ),
            404: OpenApiResponse(
                response=TrainingPlanErrorDetailSerializer,
                description="Training plan not found.",
            ),
        },
    )
    def put(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()

        serializer = TrainingPlanSerializer(training_plan, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_training_plan(
                training_plan, validated_data_as_dict(serializer)
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(TrainingPlanSerializer(updated).data)

    @extend_schema(
        tags=["Training"],
        summary="Delete training plan",
        description="Deletes a training plan owned by the authenticated user.",
        responses={
            204: OpenApiResponse(description="Training plan deleted."),
            404: OpenApiResponse(
                response=TrainingPlanErrorDetailSerializer,
                description="Training plan not found.",
            ),
        },
    )
    def delete(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()
        services.delete_training_plan(training_plan)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrainingPlanWorkoutCollectionAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PlanWorkoutSerializer

    @extend_schema(
        tags=["Training"],
        summary="List workouts for training plan",
        description="Returns the workouts that belong to a specific training plan.",
        responses={
            200: PlanWorkoutSerializer(many=True),
            404: OpenApiResponse(
                response=TrainingPlanErrorDetailSerializer,
                description="Training plan not found.",
            ),
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()
        workouts = services.list_plan_workouts(pk, str(request.user.id))
        return Response(PlanWorkoutSerializer(workouts, many=True).data)
