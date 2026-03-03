from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import APIKey, PlanType


class AccountsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="accountuser",
            email="account@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_defaults_to_free_plan(self):
        response = self.client.get("/api/v1/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["plan"], PlanType.FREE)

    def test_create_and_revoke_api_key(self):
        create_response = self.client.post("/api/v1/accounts/api-keys/", {"name": "Primary Key"})
        self.assertEqual(create_response.status_code, 201)
        self.assertIn("raw_key", create_response.data)
        key_id = create_response.data["api_key"]["id"]

        revoke_response = self.client.post(f"/api/v1/accounts/api-keys/{key_id}/revoke/")
        self.assertEqual(revoke_response.status_code, 200)
        self.assertTrue(APIKey.objects.get(id=key_id).revoked)
