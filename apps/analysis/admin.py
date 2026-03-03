from django.contrib import admin

from apps.analysis.models import AnalysisResult, TextSubmission


@admin.register(TextSubmission)
class TextSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "document", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "text")


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("submission", "final_risk_score", "credibility_score", "created_at")
