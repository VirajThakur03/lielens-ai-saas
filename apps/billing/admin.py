from django.contrib import admin

from apps.billing.models import BillingEvent


@admin.register(BillingEvent)
class BillingEventAdmin(admin.ModelAdmin):
    list_display = ("stripe_event_id", "event_type", "created_at")
    search_fields = ("stripe_event_id", "event_type")
