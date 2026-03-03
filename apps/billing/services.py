from dataclasses import dataclass

import stripe
from django.conf import settings

from apps.accounts.models import PlanType, UserProfile

stripe.api_key = settings.STRIPE_SECRET_KEY


@dataclass(frozen=True)
class CheckoutConfig:
    price_id: str
    plan: str


PLAN_TO_CHECKOUT = {
    PlanType.PRO: CheckoutConfig(price_id=settings.STRIPE_PRICE_PRO, plan=PlanType.PRO),
    PlanType.ENTERPRISE: CheckoutConfig(
        price_id=settings.STRIPE_PRICE_ENTERPRISE, plan=PlanType.ENTERPRISE
    ),
}


def get_or_create_stripe_customer(profile: UserProfile) -> str:
    if profile.stripe_customer_id:
        return profile.stripe_customer_id
    customer = stripe.Customer.create(email=profile.user.email, name=profile.user.username)
    profile.stripe_customer_id = customer["id"]
    profile.save(update_fields=["stripe_customer_id", "updated_at"])
    return customer["id"]


def create_checkout_session(profile: UserProfile, plan: str) -> str:
    config = PLAN_TO_CHECKOUT[plan]
    customer_id = get_or_create_stripe_customer(profile)
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": config.price_id, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        metadata={"user_id": profile.user_id, "plan": plan},
    )
    return session.url
