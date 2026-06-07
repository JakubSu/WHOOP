from django.urls import path

from whoop.api.views import (
    WhoopCallbackAPIView,
    WhoopConnectAPIView,
    WhoopDisconnectAPIView,
    WhoopSummaryAPIView,
)


urlpatterns = [
    path("whoop/connect-url/", WhoopConnectAPIView.as_view(), name="whoop-connect-url"),
    path("whoop/callback/", WhoopCallbackAPIView.as_view(), name="whoop-callback"),
    path("whoop/summary/", WhoopSummaryAPIView.as_view(), name="whoop-summary"),
    path("whoop/disconnect/", WhoopDisconnectAPIView.as_view(), name="whoop-disconnect"),
]
