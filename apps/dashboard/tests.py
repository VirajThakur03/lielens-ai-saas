from django.contrib.auth.models import User
from django.test import TestCase


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dashuser",
            email="dash@example.com",
            password="StrongPass123!",
        )

    def test_dashboard_contains_premium_sections(self):
        self.client.force_login(self.user)
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "API Access")
        self.assertContains(response, "Comparison Mode")
        self.assertContains(response, "Risk Heatmap Highlighting")

    def test_password_reset_pages_load(self):
        self.assertEqual(self.client.get("/accounts/password_reset/").status_code, 200)
