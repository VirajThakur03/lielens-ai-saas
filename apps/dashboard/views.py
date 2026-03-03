import json

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Q
from django.shortcuts import redirect, render

from apps.accounts.api_keys import create_api_key
from apps.accounts.models import APIKey
from apps.analysis.dispatcher import trigger_submission_analysis
from apps.analysis.services import rewrite_submission
from apps.analysis.models import SubmissionStatus, TextSubmission
from apps.dashboard.forms import DashboardSubmissionForm


@login_required
def dashboard_home(request):
    status_filter = request.GET.get("status", "all").lower()
    query = request.GET.get("q", "").strip()

    base_qs = TextSubmission.objects.filter(user=request.user)
    submissions_qs = base_qs
    if status_filter in SubmissionStatus.values:
        submissions_qs = submissions_qs.filter(status=status_filter)
    if query:
        submissions_qs = submissions_qs.filter(
            Q(text__icontains=query) | Q(cleaned_text__icontains=query) | Q(document__icontains=query)
        )

    submissions = submissions_qs.select_related("result").order_by("-created_at")[:50]
    latest_with_result = (
        base_qs.filter(status=SubmissionStatus.COMPLETED)
        .select_related("result")
        .order_by("-created_at")
        .first()
    )
    completed_results = base_qs.filter(status=SubmissionStatus.COMPLETED).select_related("result")
    risk_points = [s for s in completed_results.order_by("created_at") if hasattr(s, "result")]
    trend_labels = [s.created_at.strftime("%d %b") for s in risk_points]
    trend_risk_values = [s.result.final_risk_score for s in risk_points]

    avg_risk = 0.0
    if risk_points:
        avg_risk = round(
            base_qs.filter(status=SubmissionStatus.COMPLETED, result__isnull=False).aggregate(
                avg=Avg("result__final_risk_score")
            )["avg"]
            or 0.0,
            2,
        )

    comparison = None
    left_id = request.GET.get("compare_left")
    right_id = request.GET.get("compare_right")
    if left_id and right_id:
        left = base_qs.filter(id=left_id).select_related("result").first()
        right = base_qs.filter(id=right_id).select_related("result").first()
        if left and right and hasattr(left, "result") and hasattr(right, "result"):
            risk_change = round((right.result.final_risk_score - left.result.final_risk_score) * 100, 2)
            credibility_change = round(
                (right.result.credibility_score - left.result.credibility_score) * 100, 2
            )
            emotion_change = round(
                (right.result.emotional_intensity - left.result.emotional_intensity) * 100, 2
            )
            comparison = {
                "left_id": left.id,
                "right_id": right.id,
                "risk_change": risk_change,
                "credibility_change": credibility_change,
                "emotion_change": emotion_change,
                "improvement_summary": (
                    "Professional tone improved."
                    if risk_change < 0 and credibility_change > 0
                    else "Tone risk increased; revise exaggerated wording."
                ),
            }

    api_keys = APIKey.objects.filter(user=request.user).order_by("-created_at")

    return render(
        request,
        "dashboard/home.html",
        {
            "submissions": submissions,
            "profile": request.user.profile,
            "submission_form": DashboardSubmissionForm(),
            "latest_result": latest_with_result.result if latest_with_result else None,
            "status_filter": status_filter,
            "query": query,
            "stats": {
                "total_submissions": base_qs.count(),
                "completed_count": base_qs.filter(status=SubmissionStatus.COMPLETED).count(),
                "failed_count": base_qs.filter(status=SubmissionStatus.FAILED).count(),
                "avg_risk": avg_risk,
            },
            "trend_labels_json": json.dumps(trend_labels),
            "trend_risk_values_json": json.dumps(trend_risk_values),
            "comparison": comparison,
            "completed_submissions": risk_points,
            "api_keys": api_keys,
        },
    )


@login_required
def submit_document(request):
    if request.method != "POST":
        return redirect("/dashboard/")

    profile = request.user.profile
    if not profile.can_submit():
        messages.error(request, "Monthly analysis limit reached. Upgrade your plan.")
        return redirect("/dashboard/")

    form = DashboardSubmissionForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, form.errors.get("__all__", ["Invalid submission."])[0])
        return redirect("/dashboard/")

    submission = TextSubmission.objects.create(
        user=request.user,
        text=form.cleaned_data.get("text", ""),
        document=form.cleaned_data.get("document"),
    )
    mode = trigger_submission_analysis(submission.id)
    if mode == "async":
        messages.success(request, "Submission queued for analysis.")
    else:
        messages.success(request, "Analysis completed.")
    return redirect("/dashboard/")


@login_required
def create_api_key_view(request):
    if request.method != "POST":
        return redirect("/dashboard/")
    name = request.POST.get("name", "Dashboard Key").strip() or "Dashboard Key"
    _, raw_key = create_api_key(request.user, name=name)
    messages.success(request, f"New API key created: {raw_key}")
    return redirect("/dashboard/")


@login_required
def revoke_api_key_view(request, key_id: int):
    if request.method != "POST":
        return redirect("/dashboard/")
    key = APIKey.objects.filter(id=key_id, user=request.user).first()
    if key:
        key.revoked = True
        key.save(update_fields=["revoked"])
        messages.success(request, f"API key '{key.name}' revoked.")
    else:
        messages.error(request, "API key not found.")
    return redirect("/dashboard/")


@login_required
def rewrite_submission_view(request, submission_id: int):
    if request.method != "POST":
        return redirect("/dashboard/")

    submission = TextSubmission.objects.filter(
        id=submission_id, user=request.user, status=SubmissionStatus.COMPLETED
    ).select_related("result").first()
    if not submission:
        messages.error(request, "Completed submission not found.")
        return redirect("/dashboard/")

    try:
        result = rewrite_submission(submission)
        messages.success(request, f"Professional rewrite generated using {result.rewrite_method} mode.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("/dashboard/")
