from django.contrib.auth.models import User
from django.db import models


class SubmissionStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class TextSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    text = models.TextField(blank=True, default="")
    document = models.FileField(upload_to="submissions/%Y/%m/", blank=True, null=True)
    cleaned_text = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=16, choices=SubmissionStatus.choices, default=SubmissionStatus.QUEUED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AnalysisResult(models.Model):
    submission = models.OneToOneField(
        TextSubmission, on_delete=models.CASCADE, related_name="result"
    )
    confidence_score = models.FloatField(default=0.0)
    exaggeration_score = models.FloatField(default=0.0)
    credibility_score = models.FloatField(default=0.0)
    emotional_intensity = models.FloatField(default=0.0)
    final_risk_score = models.FloatField(default=0.0)
    ml_probability = models.FloatField(default=0.0)
    feature_snapshot = models.JSONField(default=dict)
    annotation_data = models.JSONField(default=list)
    contribution_breakdown = models.JSONField(default=dict)
    ai_summary = models.TextField(blank=True, default="")
    recommendations = models.JSONField(default=list)
    rewritten_text = models.TextField(blank=True, default="")
    rewrite_method = models.CharField(max_length=32, blank=True, default="")
    rewrite_changes = models.JSONField(default=list)
    report_file = models.FileField(upload_to="reports/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
