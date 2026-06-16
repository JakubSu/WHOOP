from training.api.views.helpers import validated_data_as_dict
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from training import services
from training.api.serializers import ExerciseSerializer


class ExerciseErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ExerciseCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExerciseSerializer

    @extend_schema(
        tags=["Training"],
        summary="List exercises",
        description="Returns the exercise library available to the authenticated user.",
        responses={200: ExerciseSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        exercises = services.list_exercises(str(request.user.id))
        return Response(ExerciseSerializer(exercises, many=True).data)

    @extend_schema(
        tags=["Training"],
        summary="Create exercise",
        description="Creates an exercise in the authenticated user's exercise library.",
        request=ExerciseSerializer,
        responses={
            201: ExerciseSerializer,
            400: OpenApiResponse(response=ExerciseErrorDetailSerializer, description="Validation error."),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = ExerciseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            exercise = services.create_exercise(validated_data_as_dict(serializer), user_id=str(request.user.id))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(ExerciseSerializer(exercise).data, status=status.HTTP_201_CREATED)


class ExerciseDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExerciseSerializer

    @extend_schema(
        tags=["Training"],
        summary="Get exercise",
        description="Returns a single exercise visible to the authenticated user.",
        responses={
            200: ExerciseSerializer,
            404: OpenApiResponse(response=ExerciseErrorDetailSerializer, description="Exercise not found."),
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        exercise = services.get_exercise(pk, str(request.user.id))
        if exercise is None:
            raise NotFound()
        return Response(ExerciseSerializer(exercise).data)

    @extend_schema(
        tags=["Training"],
        summary="Update exercise partially",
        description="Applies a partial update to an exercise.",
        request=ExerciseSerializer,
        responses={
            200: ExerciseSerializer,
            400: OpenApiResponse(response=ExerciseErrorDetailSerializer, description="Validation error."),
            404: OpenApiResponse(response=ExerciseErrorDetailSerializer, description="Exercise not found."),
        },
    )
    def patch(self, request: Request, pk: str) -> Response:
        exercise = services.get_exercise(pk, str(request.user.id))
        if exercise is None:
            raise NotFound()

        serializer = ExerciseSerializer(exercise, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_exercise(exercise, validated_data_as_dict(serializer), user_id=str(request.user.id))
        except ValueError as exc:
            raise NotFound(str(exc)) from exc
        return Response(ExerciseSerializer(updated).data)

    @extend_schema(
        tags=["Training"],
        summary="Replace exercise",
        description="Replaces an exercise with the provided payload.",
        request=ExerciseSerializer,
        responses={
            200: ExerciseSerializer,
            400: OpenApiResponse(response=ExerciseErrorDetailSerializer, description="Validation error."),
            404: OpenApiResponse(response=ExerciseErrorDetailSerializer, description="Exercise not found."),
        },
    )
    def put(self, request: Request, pk: str) -> Response:
        exercise = services.get_exercise(pk, str(request.user.id))
        if exercise is None:
            raise NotFound()

        serializer = ExerciseSerializer(exercise, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_exercise(exercise, validated_data_as_dict(serializer), user_id=str(request.user.id))
        except ValueError as exc:
            raise NotFound(str(exc)) from exc
        return Response(ExerciseSerializer(updated).data)

    @extend_schema(
        tags=["Training"],
        summary="Delete exercise",
        description="Deletes an exercise visible to the authenticated user.",
        responses={
            204: OpenApiResponse(description="Exercise deleted."),
            404: OpenApiResponse(response=ExerciseErrorDetailSerializer, description="Exercise not found."),
        },
    )
    def delete(self, request: Request, pk: str) -> Response:
        exercise = services.get_exercise(pk, str(request.user.id))
        if exercise is None:
            raise NotFound()
        try:
            services.delete_exercise(exercise, user_id=str(request.user.id))
        except ValueError as exc:
            raise NotFound(str(exc)) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)
