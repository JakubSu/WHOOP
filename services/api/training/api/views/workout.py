from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from training import services
from training.api.serializers import WorkoutExercisePageSerializer, WorkoutSerializer
from training.api.views.helpers import validated_data_as_dict


class WorkoutCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        workouts = services.list_workouts(str(request.user.id))
        return Response(WorkoutSerializer(workouts, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = WorkoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            workout = services.create_workout(validated_data_as_dict(serializer), user_id=str(request.user.id))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(WorkoutSerializer(workout).data, status=status.HTTP_201_CREATED)


class WorkoutDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()
        return Response(WorkoutSerializer(workout).data)

    def patch(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()

        serializer = WorkoutSerializer(workout, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_workout(workout, validated_data_as_dict(serializer), user_id=str(request.user.id))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(WorkoutSerializer(updated).data)

    def put(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()

        serializer = WorkoutSerializer(workout, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_workout(workout, validated_data_as_dict(serializer), user_id=str(request.user.id))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(WorkoutSerializer(updated).data)

    def delete(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()
        services.delete_workout(workout)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkoutExercisePageCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()
        workout_exercises = services.list_workout_exercises_for_workout(pk, str(request.user.id))
        return Response(WorkoutExercisePageSerializer(workout_exercises, many=True).data)
