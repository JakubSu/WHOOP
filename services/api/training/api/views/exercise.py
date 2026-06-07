from training.api.views.helpers import validated_data_as_dict
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from training import services
from training.api.serializers import ExerciseSerializer


class ExerciseCollectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        exercises = services.list_exercises()
        return Response(ExerciseSerializer(exercises, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = ExerciseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            exercise = services.create_exercise(validated_data_as_dict(serializer))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(ExerciseSerializer(exercise).data, status=status.HTTP_201_CREATED)


class ExerciseDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, pk: str) -> Response:
        exercise = services.get_exercise(pk)
        if exercise is None:
            raise NotFound()
        return Response(ExerciseSerializer(exercise).data)

    def patch(self, request: Request, pk: str) -> Response:
        exercise = services.get_exercise(pk)
        if exercise is None:
            raise NotFound()

        serializer = ExerciseSerializer(exercise, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_exercise(exercise, validated_data_as_dict(serializer))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(ExerciseSerializer(updated).data)

    def put(self, request: Request, pk: str) -> Response:
        exercise = services.get_exercise(pk)
        if exercise is None:
            raise NotFound()

        serializer = ExerciseSerializer(exercise, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.update_exercise(exercise, validated_data_as_dict(serializer))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(ExerciseSerializer(updated).data)

    def delete(self, request: Request, pk: str) -> Response:
        exercise = services.get_exercise(pk)
        if exercise is None:
            raise NotFound()
        services.delete_exercise(exercise)
        return Response(status=status.HTTP_204_NO_CONTENT)
