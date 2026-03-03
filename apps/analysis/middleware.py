from django.conf import settings
from django.http import JsonResponse

from apps.accounts.api_keys import authenticate_raw_api_key, enforce_api_key_rate_limits


class PlanEnforcementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/api/v1/analysis/submissions/" and request.method == "POST":
            if not request.user.is_authenticated:
                return JsonResponse({"detail": "Authentication required."}, status=401)
            if not request.user.profile.can_submit():
                return JsonResponse(
                    {"detail": "Monthly analysis limit reached. Please upgrade your plan."},
                    status=402,
                )
        return self.get_response(request)


class APIKeyAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/api/v1/analysis/analyze/":
            auth = request.META.get("HTTP_AUTHORIZATION", "")
            token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
            auth_result = authenticate_raw_api_key(token)
            if not auth_result:
                return JsonResponse({"detail": "Invalid or missing API key."}, status=401)

            api_key = auth_result.api_key
            api_key.reset_usage_if_new_month()
            if not api_key.can_use():
                return JsonResponse({"detail": "API key usage limit reached for current plan."}, status=402)

            allowed = enforce_api_key_rate_limits(
                api_key=api_key,
                minute_limit=settings.API_KEY_RATE_LIMIT_PER_MINUTE,
                day_limit=settings.API_KEY_RATE_LIMIT_PER_DAY,
            )
            if not allowed:
                return JsonResponse({"detail": "Rate limit exceeded for API key."}, status=429)

            request.authenticated_api_key = api_key
        return self.get_response(request)
