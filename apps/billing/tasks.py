from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.db.models import Avg
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.analysis.models import SubmissionStatus, TextSubmission


@shared_task
def reset_monthly_usage_task():
    today = timezone.now().date()
    profiles = UserProfile.objects.exclude(current_period_start__month=today.month)
    for profile in profiles:
        profile.reset_usage()


@shared_task
def send_monthly_insight_reports_task():
    now = timezone.now()
    first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_end = first_day_this_month - timedelta(seconds=1)
    previous_month_start = previous_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    profiles = UserProfile.objects.select_related("user")
    for profile in profiles:
        qs = TextSubmission.objects.filter(
            user=profile.user,
            status=SubmissionStatus.COMPLETED,
            created_at__gte=previous_month_start,
            created_at__lte=previous_month_end,
            result__isnull=False,
        ).select_related("result")

        total = qs.count()
        avg_risk = round(qs.aggregate(avg=Avg("result__final_risk_score"))["avg"] or 0.0, 3)
        if total == 0:
            most_common_issue = "No analyses submitted"
            trend_msg = "No trend available."
        else:
            issues = {"superlative": 0, "certainty": 0, "emotion": 0}
            for sub in qs:
                features = sub.result.feature_snapshot or {}
                if features.get("superlative_ratio", 0) > 0.05:
                    issues["superlative"] += 1
                if features.get("certainty_ratio", 0) > 0.04:
                    issues["certainty"] += 1
                if sub.result.emotional_intensity > 0.5:
                    issues["emotion"] += 1
            most_common_issue = max(issues, key=issues.get)
            trend_msg = (
                "Risk is trending lower." if avg_risk < 0.45 else "Risk remains elevated; revise claim-heavy language."
            )

        body = (
            f"LieLens Monthly Insight Report\n\n"
            f"Period: {previous_month_start.date()} to {previous_month_end.date()}\n"
            f"Total analyses: {total}\n"
            f"Average risk score: {avg_risk}\n"
            f"Most common issue: {most_common_issue}\n"
            f"Plan usage: {profile.analyses_used}/{profile.monthly_limit}\n"
            f"Recommendation: {trend_msg}\n"
        )

        if profile.user.email:
            send_mail(
                subject="Your LieLens Monthly Insight Report",
                message=body,
                from_email=None,
                recipient_list=[profile.user.email],
                fail_silently=True,
            )
