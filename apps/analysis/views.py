from django.http import FileResponse, Http404
from rest_framework import generics, permissions
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analysis.dispatcher import trigger_submission_analysis
from apps.analysis.models import TextSubmission
from apps.analysis.services import rewrite_submission
from apps.analysis.serializers import (
    AnalysisResultSerializer,
    SubmissionStatusSerializer,
    TextSubmissionCreateSerializer,
)


class SubmitTextAPIView(generics.CreateAPIView):
    serializer_class = TextSubmissionCreateSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def perform_create(self, serializer):
        submission = serializer.save(user=self.request.user)
        self.dispatch_mode = trigger_submission_analysis(submission.id)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        mode = getattr(self, "dispatch_mode", "sync")
        if mode == "async":
            response.data["message"] = "Submission queued for async analysis."
        else:
            response.data["message"] = "Analysis completed."
        return response


class SubmissionDetailAPIView(generics.RetrieveAPIView):
    serializer_class = SubmissionStatusSerializer
    lookup_field = "id"

    def get_queryset(self):
        return TextSubmission.objects.filter(user=self.request.user).select_related("result")


class SubmissionListAPIView(generics.ListAPIView):
    serializer_class = SubmissionStatusSerializer

    def get_queryset(self):
        return TextSubmission.objects.filter(user=self.request.user).select_related("result")


class DownloadReportAPIView(generics.GenericAPIView):
    def get(self, request, submission_id: int):
        submission = TextSubmission.objects.filter(
            id=submission_id, user=request.user
        ).select_related("result").first()
        if not submission or not hasattr(submission, "result") or not submission.result.report_file:
            raise Http404("Report not found.")
        return FileResponse(submission.result.report_file.open("rb"), as_attachment=True)


class UsageAPIView(generics.GenericAPIView):
    def get(self, request):
        profile = request.user.profile
        return Response(
            {
                "plan": profile.plan,
                "used": profile.analyses_used,
                "limit": profile.monthly_limit,
                "remaining": max(profile.monthly_limit - profile.analyses_used, 0),
            }
        )


class APIKeyAnalyzeAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request):
        api_key = getattr(request, "authenticated_api_key", None)
        if api_key is None:
            return Response({"detail": "API key authentication required."}, status=401)

        serializer = TextSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save(user=api_key.user)
        mode = trigger_submission_analysis(submission.id)
        api_key.increment_usage()

        submission.refresh_from_db()
        response = {
            "submission_id": submission.id,
            "status": submission.status,
            "dispatch_mode": mode,
        }
        if hasattr(submission, "result"):
            response["result"] = AnalysisResultSerializer(submission.result).data
        return Response(response, status=201)


class RewriteSubmissionAPIView(generics.GenericAPIView):
    def post(self, request, submission_id: int):
        submission = TextSubmission.objects.filter(
            id=submission_id, user=request.user, status="completed"
        ).select_related("result").first()
        if not submission:
            return Response({"detail": "Completed submission not found."}, status=404)
        try:
            result = rewrite_submission(submission)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(
            {
                "submission_id": submission.id,
                "rewritten_text": result.rewritten_text,
                "rewrite_method": result.rewrite_method,
                "rewrite_changes": result.rewrite_changes,
            }
        )
