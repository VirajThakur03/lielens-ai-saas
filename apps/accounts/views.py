from django.contrib.auth import login
from django.shortcuts import redirect, render
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api_keys import create_api_key
from apps.accounts.forms import SignupForm
from apps.accounts.models import APIKey
from apps.accounts.serializers import (
    APIKeyCreateSerializer,
    APIKeySerializer,
    ProfileSerializer,
    RegisterSerializer,
)


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileAPIView(generics.GenericAPIView):
    serializer_class = ProfileSerializer

    def get(self, request):
        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)


class APIKeyListCreateAPIView(APIView):
    def get(self, request):
        keys = APIKey.objects.filter(user=request.user).order_by("-created_at")
        return Response(APIKeySerializer(keys, many=True).data)

    def post(self, request):
        serializer = APIKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key, raw_key = create_api_key(request.user, serializer.validated_data["name"])
        return Response(
            {
                "api_key": APIKeySerializer(api_key).data,
                "raw_key": raw_key,
                "message": "Store this key now. It will not be shown again.",
            },
            status=201,
        )


class APIKeyRevokeAPIView(APIView):
    def post(self, request, key_id: int):
        key = APIKey.objects.filter(id=key_id, user=request.user).first()
        if not key:
            return Response({"detail": "API key not found."}, status=404)
        key.revoked = True
        key.save(update_fields=["revoked"])
        return Response({"status": "revoked"})


def register_page(request):
    if request.user.is_authenticated:
        return redirect("/dashboard/")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/dashboard/")
    else:
        form = SignupForm()
    return render(request, "registration/register.html", {"form": form})
