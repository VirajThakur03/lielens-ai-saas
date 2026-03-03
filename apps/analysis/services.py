from django.db import transaction

from apps.analysis.models import AnalysisResult, SubmissionStatus, TextSubmission
from services.document_parser import extract_text_from_uploaded_document
from services.feature_extractor import build_token_annotations, extract_features
from services.ml_model import score_probability
from services.pdf_report import build_pdf_report
from services.rewrite_engine import rewrite_professionally
from services.risk_engine import compute_risk
from services.suggestion_engine import generate_summary_and_suggestions


def sanitize_text(text: str) -> str:
    return " ".join(text.split())


def resolve_submission_text(submission: TextSubmission) -> str:
    if submission.text:
        return submission.text
    if submission.document:
        submission.document.open("rb")
        try:
            return extract_text_from_uploaded_document(submission.document)
        finally:
            submission.document.close()
    return ""


@transaction.atomic
def run_submission_analysis(submission: TextSubmission) -> AnalysisResult:
    submission.status = SubmissionStatus.PROCESSING
    raw_text = resolve_submission_text(submission)
    submission.cleaned_text = sanitize_text(raw_text)
    submission.save(update_fields=["status", "cleaned_text", "updated_at"])

    features = extract_features(submission.cleaned_text)
    annotations = build_token_annotations(submission.cleaned_text)
    ml_probability = score_probability(features)
    risk_scores = compute_risk(features, ml_probability)
    contribution_breakdown = risk_scores.pop("contribution_breakdown", {})
    summary, recommendations = generate_summary_and_suggestions(risk_scores, features)

    result = AnalysisResult.objects.create(
        submission=submission,
        ml_probability=ml_probability,
        feature_snapshot=features,
        annotation_data=annotations,
        contribution_breakdown=contribution_breakdown,
        ai_summary=summary,
        recommendations=recommendations,
        **risk_scores,
    )

    report_name = build_pdf_report(submission, result)
    result.report_file = report_name
    result.save(update_fields=["report_file"])

    submission.status = SubmissionStatus.COMPLETED
    submission.save(update_fields=["status", "updated_at"])
    submission.user.profile.increment_usage()
    return result


@transaction.atomic
def rewrite_submission(submission: TextSubmission) -> AnalysisResult:
    if not hasattr(submission, "result"):
        raise ValueError("Submission has no analysis result to rewrite.")

    source_text = submission.cleaned_text or submission.text
    if not source_text:
        raise ValueError("No text available to rewrite.")

    rewrite = rewrite_professionally(source_text)
    result = submission.result
    result.rewritten_text = str(rewrite["rewritten_text"])
    result.rewrite_method = str(rewrite["rewrite_method"])
    result.rewrite_changes = list(rewrite["rewrite_changes"])
    result.save(update_fields=["rewritten_text", "rewrite_method", "rewrite_changes"])
    return result
