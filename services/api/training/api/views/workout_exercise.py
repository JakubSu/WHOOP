from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from training import services
from training.api.serializers import WorkoutExerciseSerializer
from training.api.views.helpers import validated_data_as_dict


class WorkoutExerciseCollectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        workout_exercises = services.list_workout_exercises()
        return Response(WorkoutExerciseSerializer(workout_exercises, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = WorkoutExerciseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            workout_exercise = services.create_workout_exercise(validated_data_as_dict(serializer))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "Workout exercise position must be unique within a workout."}) from exc
        return Response(WorkoutExerciseSerializer(workout_exercise).data, status=status.HTTP_201_CREATED)


class WorkoutExerciseDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, pk: str) -> Response:
        workout_exercise = services.get_workout_exercise(pk)
        if workout_exercise is None:
            raise NotFound()
        return Response(WorkoutExerciseSerializer(workout_exercise).data)

    def patch(self, request: Request, pk: str) -> Response:
        workout_exercise = services.get_workout_exercise(pk)
        if workout_exercise is None:
            raise NotFound()

        serializer = WorkoutExerciseSerializer(workout_exercise, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_workout_exercise(workout_exercise, validated_data_as_dict(serializer))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "Workout exercise position must be unique within a workout."}) from exc
        return Response(WorkoutExerciseSerializer(updated).data)

    def put(self, request: Request, pk: str) -> Response:
        workout_exercise = services.get_workout_exercise(pk)
        if workout_exercise is None:
            raise NotFound()

        serializer = WorkoutExerciseSerializer(workout_exercise, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_workout_exercise(workout_exercise, validated_data_as_dict(serializer))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "Workout exercise position must be unique within a workout."}) from exc
        return Response(WorkoutExerciseSerializer(updated).data)

    def delete(self, request: Request, pk: str) -> Response:
        workout_exercise = services.get_workout_exercise(pk)
        if workout_exercise is None:
            raise NotFound()
        services.delete_workout_exercise(workout_exercise)
        return Response(status=status.HTTP_204_NO_CONTENT)
