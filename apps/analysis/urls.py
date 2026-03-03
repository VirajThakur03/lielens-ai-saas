from django.urls import path

from apps.analysis.views import (
    APIKeyAnalyzeAPIView,
    DownloadReportAPIView,
    RewriteSubmissionAPIView,
    SubmissionDetailAPIView,
    SubmissionListAPIView,
    SubmitTextAPIView,
    UsageAPIView,
)


urlpatterns = [
    path("submissions/", SubmitTextAPIView.as_view(), name="submit-text"),
    path("submissions/history/", SubmissionListAPIView.as_view(), name="submission-history"),
    path("submissions/<int:id>/", SubmissionDetailAPIView.as_view(), name="submission-detail"),
    path("submissions/<int:submission_id>/report/", DownloadReportAPIView.as_view(), name="report"),
    path("submissions/<int:submission_id>/rewrite/", RewriteSubmissionAPIView.as_view(), name="rewrite"),
    path("usage/", UsageAPIView.as_view(), name="usage"),
    path("analyze/", APIKeyAnalyzeAPIView.as_view(), name="analyze-api-key"),
]
