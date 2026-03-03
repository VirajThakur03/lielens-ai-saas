import json

import stripe
from django.conf import settings
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import PlanType, UserProfile
from apps.billing.models import BillingEvent
from apps.billing.services import create_checkout_session

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionAPIView(APIView):
    def post(self, request):
        plan = request.data.get("plan")
        if plan not in [PlanType.PRO, PlanType.ENTERPRISE]:
            return Response({"detail": "Invalid plan."}, status=400)
        if not settings.STRIPE_SECRET_KEY:
            return Response({"detail": "Stripe is not configured."}, status=400)
        checkout_url = create_checkout_session(request.user.profile, plan)
        return Response({"checkout_url": checkout_url})


class StripeWebhookAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        secret = settings.STRIPE_WEBHOOK_SECRET
        try:
            event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=secret)
        except ValueError:
            return Response({"detail": "Invalid payload"}, status=400)
        except stripe.error.SignatureVerificationError:
            return Response({"detail": "Invalid signature"}, status=400)

        event_id = event["id"]
        if BillingEvent.objects.filter(stripe_event_id=event_id).exists():
            return Response({"status": "duplicate"})

        event_type = event["type"]
        data = event["data"]["object"]
        user = None
        metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
        user_id = metadata.get("user_id")
        if user_id:
            profile = UserProfile.objects.filter(user_id=user_id).first()
            user = profile.user if profile else None
            if profile and event_type in ("checkout.session.completed", "customer.subscription.updated"):
                plan = metadata.get("plan", PlanType.PRO)
                if plan in [PlanType.PRO, PlanType.ENTERPRISE]:
                    profile.plan = plan
                    profile.save(update_fields=["plan", "updated_at"])

        BillingEvent.objects.create(
            user=user,
            event_type=event_type,
            stripe_event_id=event_id,
            payload=json.loads(payload.decode("utf-8")),
        )
        return Response({"status": "ok"})
