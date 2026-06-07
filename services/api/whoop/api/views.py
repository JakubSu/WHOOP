from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from whoop import services
from whoop.api.serializers import WhoopSummarySerializer
from whoop.exceptions import WhoopConnectionNotFound
from whoop.workflows.summary import disconnected_summary


class WhoopConnectAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        payload = services.create_build_connect_url_service().execute(
            user_id=str(request.user.id)
        )
        return Response(payload)


class WhoopCallbackAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response | HttpResponseRedirect:
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            raise ValidationError({"detail": "Missing WHOOP authorization code."})
        if not state:
            raise ValidationError({"detail": "Invalid WHOOP OAuth state."})

        try:
            services.create_complete_connection_service().execute(state=state, code=code)
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        if settings.WHOOP_FRONTEND_SUCCESS_URL:
            return redirect(settings.WHOOP_FRONTEND_SUCCESS_URL)
        return Response({"connected": True})


class WhoopSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        try:
            summary = services.create_summary_service().execute(str(request.user.id))
        except WhoopConnectionNotFound:
            summary = disconnected_summary()
            serializer = WhoopSummarySerializer(summary)
            return Response(serializer.data, status=status.HTTP_404_NOT_FOUND)

        serializer = WhoopSummarySerializer(summary)
        return Response(serializer.data)


class WhoopDisconnectAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        disconnected = services.create_disconnect_service().execute(str(request.user.id))
        if not disconnected:
            raise NotFound("WHOOP is not connected.")
        return Response(status=status.HTTP_204_NO_CONTENT)
