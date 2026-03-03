from django.contrib.auth.models import User
from rest_framework import serializers

from apps.accounts.models import APIKey, UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    monthly_limit = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "username",
            "email",
            "plan",
            "analyses_used",
            "monthly_limit",
            "current_period_start",
        )


class APIKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80, required=False, default="Default Key")


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = (
            "id",
            "name",
            "prefix",
            "revoked",
            "monthly_used",
            "current_period_start",
            "last_used_at",
            "created_at",
        )
