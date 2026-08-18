from django.urls import path

from users.api.views import (
    CurrentUserProfileAPIView,
    DemoSessionAPIView,
    LoginAPIView,
    LogoutAPIView,
    RefreshAPIView,
    RegisterAPIView,
)

urlpatterns = [
    path("users/register/", RegisterAPIView.as_view(), name="user-register"),
    path("users/login/", LoginAPIView.as_view(), name="user-login"),
    path("users/demo-session/", DemoSessionAPIView.as_view(), name="user-demo-session"),
    path("users/token/refresh/", RefreshAPIView.as_view(), name="user-token-refresh"),
    path("users/logout/", LogoutAPIView.as_view(), name="user-logout"),
    path("users/me/", CurrentUserProfileAPIView.as_view(), name="user-me"),
]
