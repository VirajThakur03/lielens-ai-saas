import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)


class ApiExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            logger.exception("Unhandled exception", extra={"path": request.path})
            if request.path.startswith("/api/"):
                return JsonResponse({"detail": "Internal server error."}, status=500)
            raise exc
