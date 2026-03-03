from django.urls import path

from apps.dashboard.views import (
    create_api_key_view,
    dashboard_home,
    rewrite_submission_view,
    revoke_api_key_view,
    submit_document,
)

urlpatterns = [
    path("", dashboard_home, name="dashboard-home"),
    path("submit/", submit_document, name="dashboard-submit"),
    path("rewrite/<int:submission_id>/", rewrite_submission_view, name="dashboard-rewrite"),
    path("api-keys/create/", create_api_key_view, name="dashboard-api-key-create"),
    path("api-keys/<int:key_id>/revoke/", revoke_api_key_view, name="dashboard-api-key-revoke"),
]
