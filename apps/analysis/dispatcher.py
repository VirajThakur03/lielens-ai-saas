import logging

from django.conf import settings

from apps.analysis.tasks import process_submission_task

logger = logging.getLogger(__name__)


def trigger_submission_analysis(submission_id: int) -> str:
    mode = getattr(settings, "ANALYSIS_DISPATCH_MODE", "sync")

    if mode == "sync":
        process_submission_task.apply(args=[submission_id])
        return "sync"

    try:
        process_submission_task.delay(submission_id)
        return "async"
    except Exception:
        logger.exception("Async dispatch failed; using sync fallback")
        process_submission_task.apply(args=[submission_id])
        return "sync-fallback"
