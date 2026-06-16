from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from training import services
from training.api.serializers import WorkoutExercisePageSerializer, WorkoutSerializer
from training.api.views.helpers import validated_data_as_dict


class WorkoutErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class WorkoutCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WorkoutSerializer

    @extend_schema(
        tags=["Training"],
        summary="List workouts",
        description="Returns all workouts owned by the authenticated user.",
        responses={200: WorkoutSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        workouts = services.list_workouts(str(request.user.id))
        return Response(WorkoutSerializer(workouts, many=True).data)

    @extend_schema(
        tags=["Training"],
        summary="Create workout",
        description="Creates a workout for the authenticated user.",
        request=WorkoutSerializer,
        responses={
            201: WorkoutSerializer,
            400: OpenApiResponse(response=WorkoutErrorDetailSerializer, description="Validation error."),
        },
    )
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
    serializer_class = WorkoutSerializer

    @extend_schema(
        tags=["Training"],
        summary="Get workout",
        description="Returns a single workout owned by the authenticated user.",
        responses={
            200: WorkoutSerializer,
            404: OpenApiResponse(response=WorkoutErrorDetailSerializer, description="Workout not found."),
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()
        return Response(WorkoutSerializer(workout).data)

    @extend_schema(
        tags=["Training"],
        summary="Update workout partially",
        description="Applies a partial update to a workout.",
        request=WorkoutSerializer,
        responses={
            200: WorkoutSerializer,
            400: OpenApiResponse(response=WorkoutErrorDetailSerializer, description="Validation error."),
            404: OpenApiResponse(response=WorkoutErrorDetailSerializer, description="Workout not found."),
        },
    )
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

    @extend_schema(
        tags=["Training"],
        summary="Replace workout",
        description="Replaces the workout with the provided payload.",
        request=WorkoutSerializer,
        responses={
            200: WorkoutSerializer,
            400: OpenApiResponse(response=WorkoutErrorDetailSerializer, description="Validation error."),
            404: OpenApiResponse(response=WorkoutErrorDetailSerializer, description="Workout not found."),
        },
    )
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

    @extend_schema(
        tags=["Training"],
        summary="Delete workout",
        description="Deletes a workout owned by the authenticated user.",
        responses={
            204: OpenApiResponse(description="Workout deleted."),
            404: OpenApiResponse(response=WorkoutErrorDetailSerializer, description="Workout not found."),
        },
    )
    def delete(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()
        services.delete_workout(workout)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkoutExercisePageCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WorkoutExercisePageSerializer

    @extend_schema(
        tags=["Training"],
        summary="List workout exercises for workout",
        description="Returns the expanded workout exercise entries for a specific workout.",
        responses={
            200: WorkoutExercisePageSerializer(many=True),
            404: OpenApiResponse(response=WorkoutErrorDetailSerializer, description="Workout not found."),
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        workout = services.get_workout(pk, str(request.user.id))
        if workout is None:
            raise NotFound()
        workout_exercises = services.list_workout_exercises_for_workout(pk, str(request.user.id))
        return Response(WorkoutExercisePageSerializer(workout_exercises, many=True).data)
