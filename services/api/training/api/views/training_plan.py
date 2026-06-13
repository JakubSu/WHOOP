from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from training import services
from training.api.serializers import PlanWorkoutSerializer, TrainingPlanSerializer
from training.api.views.helpers import validated_data_as_dict


class TrainingPlanCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        training_plans = services.list_training_plans(str(request.user.id))
        return Response(TrainingPlanSerializer(training_plans, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = TrainingPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            training_plan = services.create_training_plan(validated_data_as_dict(serializer), user_id=str(request.user.id))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(TrainingPlanSerializer(training_plan).data, status=status.HTTP_201_CREATED)


class TrainingPlanDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()
        return Response(TrainingPlanSerializer(training_plan).data)

    def patch(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()

        serializer = TrainingPlanSerializer(training_plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_training_plan(training_plan, validated_data_as_dict(serializer))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(TrainingPlanSerializer(updated).data)

    def put(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()

        serializer = TrainingPlanSerializer(training_plan, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_training_plan(training_plan, validated_data_as_dict(serializer))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(TrainingPlanSerializer(updated).data)

    def delete(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()
        services.delete_training_plan(training_plan)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrainingPlanWorkoutCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        training_plan = services.get_training_plan(pk, str(request.user.id))
        if training_plan is None:
            raise NotFound()
        workouts = services.list_plan_workouts(pk, str(request.user.id))
        return Response(PlanWorkoutSerializer(workouts, many=True).data)
