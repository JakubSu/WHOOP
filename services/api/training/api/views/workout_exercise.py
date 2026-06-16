from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from training import services
from training.api.serializers import WorkoutExerciseSerializer
from training.api.views.helpers import validated_data_as_dict


class WorkoutExerciseErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class WorkoutExerciseCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WorkoutExerciseSerializer

    @extend_schema(
        tags=["Training"],
        summary="List workout exercises",
        description="Returns all workout exercise entries visible to the authenticated user.",
        responses={200: WorkoutExerciseSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        workout_exercises = services.list_workout_exercises(str(request.user.id))
        return Response(WorkoutExerciseSerializer(workout_exercises, many=True).data)

    @extend_schema(
        tags=["Training"],
        summary="Create workout exercise",
        description="Creates a workout exercise entry for the authenticated user.",
        request=WorkoutExerciseSerializer,
        responses={
            201: WorkoutExerciseSerializer,
            400: OpenApiResponse(response=WorkoutExerciseErrorDetailSerializer, description="Validation error."),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = WorkoutExerciseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            workout_exercise = services.create_workout_exercise(validated_data_as_dict(serializer), user_id=str(request.user.id))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(WorkoutExerciseSerializer(workout_exercise).data, status=status.HTTP_201_CREATED)


class WorkoutExerciseDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WorkoutExerciseSerializer

    @extend_schema(
        tags=["Training"],
        summary="Get workout exercise",
        description="Returns a single workout exercise entry visible to the authenticated user.",
        responses={
            200: WorkoutExerciseSerializer,
            404: OpenApiResponse(response=WorkoutExerciseErrorDetailSerializer, description="Workout exercise not found."),
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        workout_exercise = services.get_workout_exercise(pk, str(request.user.id))
        if workout_exercise is None:
            raise NotFound()
        return Response(WorkoutExerciseSerializer(workout_exercise).data)

    @extend_schema(
        tags=["Training"],
        summary="Update workout exercise partially",
        description="Applies a partial update to a workout exercise entry.",
        request=WorkoutExerciseSerializer,
        responses={
            200: WorkoutExerciseSerializer,
            400: OpenApiResponse(response=WorkoutExerciseErrorDetailSerializer, description="Validation error."),
            404: OpenApiResponse(response=WorkoutExerciseErrorDetailSerializer, description="Workout exercise not found."),
        },
    )
    def patch(self, request: Request, pk: str) -> Response:
        workout_exercise = services.get_workout_exercise(pk, str(request.user.id))
        if workout_exercise is None:
            raise NotFound()

        serializer = WorkoutExerciseSerializer(workout_exercise, data=request.data, partial=True)
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
        summary="Replace workout exercise",
        description="Replaces a workout exercise entry with the provided payload.",
        request=WorkoutExerciseSerializer,
        responses={
            200: WorkoutExerciseSerializer,
            400: OpenApiResponse(response=WorkoutExerciseErrorDetailSerializer, description="Validation error."),
            404: OpenApiResponse(response=WorkoutExerciseErrorDetailSerializer, description="Workout exercise not found."),
        },
    )
    def put(self, request: Request, pk: str) -> Response:
        workout_exercise = services.get_workout_exercise(pk, str(request.user.id))
        if workout_exercise is None:
            raise NotFound()

        serializer = WorkoutExerciseSerializer(workout_exercise, data=request.data)
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
        summary="Delete workout exercise",
        description="Deletes a workout exercise entry visible to the authenticated user.",
        responses={
            204: OpenApiResponse(description="Workout exercise deleted."),
            404: OpenApiResponse(response=WorkoutExerciseErrorDetailSerializer, description="Workout exercise not found."),
        },
    )
    def delete(self, request: Request, pk: str) -> Response:
        workout_exercise = services.get_workout_exercise(pk, str(request.user.id))
        if workout_exercise is None:
            raise NotFound()
        try:
            services.delete_workout_exercise(workout_exercise, user_id=str(request.user.id))
        except ValueError as exc:
            raise NotFound(str(exc)) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)
