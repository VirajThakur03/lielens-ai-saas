from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    APIKeyListCreateAPIView,
    APIKeyRevokeAPIView,
    ProfileAPIView,
    RegisterAPIView,
)


urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", ProfileAPIView.as_view(), name="profile"),
    path("api-keys/", APIKeyListCreateAPIView.as_view(), name="api-keys"),
    path("api-keys/<int:key_id>/revoke/", APIKeyRevokeAPIView.as_view(), name="api-key-revoke"),
]
