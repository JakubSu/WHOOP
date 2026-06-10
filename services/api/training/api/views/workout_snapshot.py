from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from training import services
from training.api.serializers import WorkoutSnapshotWriteSerializer
from training.api.views.helpers import validated_data_as_dict


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict."
    default_code = "conflict"


class WorkoutSnapshotCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        snapshots = services.list_workout_snapshots(str(request.user.id))
        return Response([snapshot.to_dict() for snapshot in snapshots])

    def post(self, request: Request) -> Response:
        serializer = WorkoutSnapshotWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = validated_data_as_dict(serializer)
        if "name" not in data:
            raise ValidationError({"name": "This field is required."})

        try:
            snapshot = services.create_workout_snapshot(data, user_id=str(request.user.id))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "Workout exercise position must be unique within a workout."}) from exc
        return Response(snapshot.to_dict(), status=status.HTTP_201_CREATED)


class WorkoutSnapshotDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        snapshot = services.get_workout_snapshot(pk, str(request.user.id))
        if snapshot is None:
            raise NotFound()
        return Response(snapshot.to_dict())

    def patch(self, request: Request, pk: str) -> Response:
        return self._update(request, pk)

    def put(self, request: Request, pk: str) -> Response:
        return self._update(request, pk)

    def delete(self, request: Request, pk: str) -> Response:
        try:
            services.delete_workout_snapshot(pk, user_id=str(request.user.id))
        except ValueError as exc:
            raise NotFound(str(exc)) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update(self, request: Request, pk: str) -> Response:
        serializer = WorkoutSnapshotWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            snapshot = services.update_workout_snapshot(
                pk,
                validated_data_as_dict(serializer),
                user_id=str(request.user.id),
            )
        except services.StaleWorkoutSnapshotVersion as exc:
            raise Conflict(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "Workout exercise position must be unique within a workout."}) from exc
        return Response(snapshot.to_dict())
