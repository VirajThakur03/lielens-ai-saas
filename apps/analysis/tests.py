from django.test import Client, TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.accounts.api_keys import create_api_key
from apps.analysis.models import AnalysisResult, SubmissionStatus, TextSubmission
from apps.analysis.services import run_submission_analysis


class AnalysisPipelineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="analyst",
            email="analyst@example.com",
            password="StrongPass123!",
        )

    def test_run_submission_analysis_generates_scores_and_metadata(self):
        submission = TextSubmission.objects.create(
            user=self.user,
            text="I am the best engineer and always deliver perfect results for every team.",
        )

        result = run_submission_analysis(submission)
        submission.refresh_from_db()

        self.assertEqual(submission.status, SubmissionStatus.COMPLETED)
        self.assertIsInstance(result, AnalysisResult)
        self.assertGreaterEqual(result.final_risk_score, 0.0)
        self.assertLessEqual(result.final_risk_score, 1.0)
        self.assertTrue(len(result.annotation_data) > 0)
        self.assertIn("ml_influence_pct", result.contribution_breakdown)

    def test_api_key_analyze_endpoint_returns_result(self):
        api_key, raw_key = create_api_key(self.user, name="CI Key")
        self.assertFalse(api_key.revoked)

        client = Client()
        response = client.post(
            "/api/v1/analysis/analyze/",
            data={"text": "Our platform will always dominate the market with unmatched quality."},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw_key}",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertIn("submission_id", payload)
        self.assertIn("result", payload)
        self.assertIn("final_risk_score", payload["result"])

    def test_rewrite_endpoint_generates_professional_text(self):
        submission = TextSubmission.objects.create(
            user=self.user,
            text="I am the best engineer and always deliver unmatched outcomes.",
        )
        run_submission_analysis(submission)

        api_client = APIClient()
        api_client.force_authenticate(user=self.user)
        response = api_client.post(f"/api/v1/analysis/submissions/{submission.id}/rewrite/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("rewritten_text", payload)
        self.assertTrue(payload["rewritten_text"])
