from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class PlanType(models.TextChoices):
    FREE = "free", "Free"
    PRO = "pro", "Pro"
    ENTERPRISE = "enterprise", "Enterprise"


PLAN_LIMITS = {
    PlanType.FREE: 5,
    PlanType.PRO: 100,
    PlanType.ENTERPRISE: 999999999,
}


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    plan = models.CharField(max_length=16, choices=PlanType.choices, default=PlanType.FREE)
    analyses_used = models.PositiveIntegerField(default=0)
    current_period_start = models.DateField(default=timezone.localdate)
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def monthly_limit(self) -> int:
        return PLAN_LIMITS[self.plan]

    def can_submit(self) -> bool:
        if self.plan == PlanType.ENTERPRISE:
            return True
        return self.analyses_used < self.monthly_limit

    def increment_usage(self) -> None:
        self.analyses_used += 1
        self.save(update_fields=["analyses_used", "updated_at"])

    def reset_usage(self) -> None:
        self.analyses_used = 0
        self.current_period_start = timezone.now().date()
        self.save(update_fields=["analyses_used", "current_period_start", "updated_at"])


class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=80, default="Default Key")
    prefix = models.CharField(max_length=16, db_index=True)
    key_hash = models.CharField(max_length=128, unique=True)
    revoked = models.BooleanField(default=False)
    monthly_used = models.PositiveIntegerField(default=0)
    current_period_start = models.DateField(default=timezone.localdate)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username}:{self.name}:{self.prefix}"

    @property
    def monthly_limit(self) -> int:
        return self.user.profile.monthly_limit

    def can_use(self) -> bool:
        if self.revoked:
            return False
        if self.user.profile.plan == PlanType.ENTERPRISE:
            return True
        return self.monthly_used < self.monthly_limit

    def reset_usage_if_new_month(self):
        now = timezone.now().date()
        if self.current_period_start.month != now.month or self.current_period_start.year != now.year:
            self.monthly_used = 0
            self.current_period_start = now
            self.save(update_fields=["monthly_used", "current_period_start"])

    def increment_usage(self):
        self.reset_usage_if_new_month()
        self.monthly_used += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=["monthly_used", "last_used_at"])
