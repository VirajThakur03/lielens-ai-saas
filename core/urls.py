from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from apps.accounts.views import register_page

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/register/", register_page, name="register-page"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/analysis/", include("apps.analysis.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("", lambda request: redirect("/dashboard/")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
