import logging

from celery import shared_task

from apps.analysis.models import SubmissionStatus, TextSubmission
from apps.analysis.services import run_submission_analysis

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_submission_task(self, submission_id: int):
    submission = TextSubmission.objects.get(id=submission_id)
    try:
        run_submission_analysis(submission)
    except Exception:
        logger.exception("Failed to process submission", extra={"submission_id": submission_id})
        submission.status = SubmissionStatus.FAILED
        submission.save(update_fields=["status", "updated_at"])
        raise
