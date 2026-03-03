from django.urls import path

from apps.billing.views import CreateCheckoutSessionAPIView, StripeWebhookAPIView


urlpatterns = [
    path("checkout/", CreateCheckoutSessionAPIView.as_view(), name="checkout"),
    path("webhooks/stripe/", StripeWebhookAPIView.as_view(), name="stripe-webhook"),
]
