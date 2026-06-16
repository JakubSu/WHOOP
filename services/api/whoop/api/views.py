from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from whoop import services
from whoop.api.serializers import WhoopCallbackResultSerializer, WhoopConnectUrlSerializer, WhoopSummarySerializer
from whoop.exceptions import WhoopConnectionNotFound
from whoop.workflows.summary import disconnected_summary


ErrorDetailSerializer = inline_serializer(
    name="WhoopErrorDetail",
    fields={"detail": serializers.CharField()},
)

EmptyRequestSerializer = inline_serializer(
    name="WhoopEmptyRequest",
    fields={},
)


class WhoopConnectAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WhoopConnectUrlSerializer

    @extend_schema(
        tags=["WHOOP"],
        summary="Create WHOOP connect URL",
        description="Builds a WHOOP OAuth authorization URL for the authenticated user. An optional frontend success URL can be carried through the OAuth flow.",
        parameters=[
            OpenApiParameter(
                name="success_url",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Optional frontend URL to redirect to after a successful WHOOP callback.",
            ),
        ],
        responses={
            200: WhoopConnectUrlSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Invalid query parameter or WHOOP connection setup error."),
        },
        examples=[
            OpenApiExample(
                "Connect URL response",
                response_only=True,
                value={
                    "connect_url": "https://api.prod.whoop.com/oauth/oauth2/auth?client_id=...&state=secure-state",
                },
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        frontend_success_url = request.query_params.get("success_url", "")
        try:
            payload = services.create_build_connect_url_service().execute(
                user_id=str(request.user.id),
                frontend_success_url=frontend_success_url,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(payload)


class WhoopCallbackAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = WhoopCallbackResultSerializer

    @extend_schema(
        tags=["WHOOP"],
        summary="WHOOP OAuth callback",
        description="Completes the WHOOP OAuth flow. If a frontend success URL is configured, this endpoint redirects there; otherwise it returns a small JSON confirmation payload.",
        parameters=[
            OpenApiParameter(
                name="code",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="WHOOP OAuth authorization code returned by WHOOP.",
            ),
            OpenApiParameter(
                name="state",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Opaque WHOOP OAuth state value issued by the application.",
            ),
        ],
        responses={
            200: WhoopCallbackResultSerializer,
            302: OpenApiResponse(description="Redirect to the frontend success URL."),
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Missing query parameters or invalid WHOOP callback state."),
        },
        examples=[
            OpenApiExample(
                "Callback fallback response",
                response_only=True,
                value={"connected": True},
            ),
        ],
    )
    def get(self, request: Request) -> Response | HttpResponseRedirect:
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            raise ValidationError({"detail": "Missing WHOOP authorization code."})
        if not state:
            raise ValidationError({"detail": "Invalid WHOOP OAuth state."})

        try:
            mapping = services.create_complete_connection_service().execute(state=state, code=code)
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        if mapping.frontend_success_url:
            return redirect(mapping.frontend_success_url)
        if settings.WHOOP_FRONTEND_SUCCESS_URL:
            return redirect(settings.WHOOP_FRONTEND_SUCCESS_URL)
        return Response({"connected": True})


class WhoopSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WhoopSummarySerializer

    @extend_schema(
        tags=["WHOOP"],
        summary="Get WHOOP summary",
        description="Returns a summary of the authenticated user's latest WHOOP data. If WHOOP is not connected, a disconnected summary is returned with a 404 status.",
        responses={
            200: WhoopSummarySerializer,
            404: OpenApiResponse(response=WhoopSummarySerializer, description="WHOOP is not connected for the authenticated user."),
        },
    )
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
    serializer_class = EmptyRequestSerializer

    @extend_schema(
        tags=["WHOOP"],
        summary="Disconnect WHOOP",
        description="Deletes the authenticated user's WHOOP connection.",
        request=None,
        responses={
            204: OpenApiResponse(description="WHOOP connection removed."),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="WHOOP was not connected."),
        },
    )
    def post(self, request: Request) -> Response:
        disconnected = services.create_disconnect_service().execute(str(request.user.id))
        if not disconnected:
            raise NotFound("WHOOP is not connected.")
        return Response(status=status.HTTP_204_NO_CONTENT)
