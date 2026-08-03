from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from training import services
from training.api.serializers import (
    WorkoutErrorDetailSerializer,
    WorkoutExercisePageSerializer,
    WorkoutExerciseRequestSerializer,
    WorkoutExerciseSerializer,
)
from training.api.views.helpers import validated_data_as_dict


class WorkoutExercisePageCollectionAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WorkoutExercisePageSerializer

    @extend_schema(
        tags=["Training"],
        summary="List workout exercises for workout",
        description="Returns the expanded workout exercise entries for a specific workout.",
        responses={
            200: WorkoutExercisePageSerializer(many=True),
            404: OpenApiResponse(
                response=WorkoutErrorDetailSerializer, description="Workout not found."
            ),
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()
        workout_exercises = services.list_workout_exercises_for_workout(
            pk, str(request.user.id)
        )
        return Response(
            WorkoutExercisePageSerializer(workout_exercises, many=True).data
        )

    @extend_schema(
        tags=["Training"],
        summary="Create workout exercise for workout",
        description="Creates a workout exercise entry under a specific workout.",
        request=WorkoutExerciseRequestSerializer,
        responses={
            201: WorkoutExerciseSerializer,
            400: OpenApiResponse(
                response=WorkoutErrorDetailSerializer, description="Validation error."
            ),
            404: OpenApiResponse(
                response=WorkoutErrorDetailSerializer, description="Workout not found."
            ),
        },
    )
    def post(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()

        serializer = WorkoutExerciseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = validated_data_as_dict(serializer)
        data["workout"] = str(workout.id)
        try:
            workout_exercise = services.create_workout_exercise(
                data, user_id=str(request.user.id)
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(
            WorkoutExerciseSerializer(workout_exercise).data,
            status=status.HTTP_201_CREATED,
        )


class WorkoutExercisePageDetailAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WorkoutExerciseSerializer

    def _get_workout_exercise(
        self, request: Request, pk: str, workout_exercise_id: str
    ):
        workout_exercise = services.get_workout_exercise_for_workout(
            pk, workout_exercise_id, str(request.user.id)
        )
        if workout_exercise is None:
            raise NotFound()
        return workout_exercise

    @extend_schema(
        tags=["Training"],
        summary="Get workout exercise for workout",
        description="Returns a single workout exercise entry for a specific workout.",
        responses={
            200: WorkoutExerciseSerializer,
            404: OpenApiResponse(
                response=WorkoutErrorDetailSerializer,
                description="Workout or workout exercise not found.",
            ),
        },
    )
    def get(self, request: Request, pk: str, workout_exercise_id: str) -> Response:
        workout_exercise = self._get_workout_exercise(request, pk, workout_exercise_id)
        return Response(WorkoutExerciseSerializer(workout_exercise).data)

    @extend_schema(
        tags=["Training"],
        summary="Update workout exercise for workout partially",
        description="Applies a partial update to a workout exercise entry.",
        request=WorkoutExerciseRequestSerializer,
        responses={
            200: WorkoutExerciseSerializer,
            400: OpenApiResponse(
                response=WorkoutErrorDetailSerializer, description="Validation error."
            ),
            404: OpenApiResponse(
                response=WorkoutErrorDetailSerializer,
                description="Workout or workout exercise not found.",
            ),
        },
    )
    def patch(self, request: Request, pk: str, workout_exercise_id: str) -> Response:
        workout_exercise = self._get_workout_exercise(request, pk, workout_exercise_id)
        serializer = WorkoutExerciseRequestSerializer(
            workout_exercise, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_workout_exercise(
                workout_exercise,
                validated_data_as_dict(serializer),
                user_id=str(request.user.id),
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(WorkoutExerciseSerializer(updated).data)

    @extend_schema(
        tags=["Training"],
        summary="Replace workout exercise for workout",
        description="Replaces a workout exercise entry under a specific workout.",
        request=WorkoutExerciseRequestSerializer,
        responses={
            200: WorkoutExerciseSerializer,
            400: OpenApiResponse(
                response=WorkoutErrorDetailSerializer, description="Validation error."
            ),
            404: OpenApiResponse(
                response=WorkoutErrorDetailSerializer,
                description="Workout or workout exercise not found.",
            ),
        },
    )
    def put(self, request: Request, pk: str, workout_exercise_id: str) -> Response:
        workout_exercise = self._get_workout_exercise(request, pk, workout_exercise_id)
        serializer = WorkoutExerciseRequestSerializer(
            workout_exercise, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_workout_exercise(
                workout_exercise,
                validated_data_as_dict(serializer),
                user_id=str(request.user.id),
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(WorkoutExerciseSerializer(updated).data)

    @extend_schema(
        tags=["Training"],
        summary="Delete workout exercise from workout",
        description="Deletes a workout exercise entry under a specific workout.",
        responses={
            204: OpenApiResponse(description="Workout exercise deleted."),
            404: OpenApiResponse(
                response=WorkoutErrorDetailSerializer,
                description="Workout or workout exercise not found.",
            ),
        },
    )
    def delete(self, request: Request, pk: str, workout_exercise_id: str) -> Response:
        workout_exercise = self._get_workout_exercise(request, pk, workout_exercise_id)
        services.delete_workout_exercise(workout_exercise, user_id=str(request.user.id))
        return Response(status=status.HTTP_204_NO_CONTENT)
