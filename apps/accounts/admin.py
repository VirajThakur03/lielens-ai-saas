from django.contrib import admin

from apps.accounts.models import APIKey, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "analyses_used", "current_period_start")
    search_fields = ("user__username", "user__email")


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "prefix", "revoked", "monthly_used", "created_at")
    list_filter = ("revoked", "created_at")
    search_fields = ("user__username", "name", "prefix")
