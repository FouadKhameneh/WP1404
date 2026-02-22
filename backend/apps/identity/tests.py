from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class IdentityAuthApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="detective01",
            email="detective01@example.com",
            password="StrongPass123!",
            phone="09120000001",
            national_id="0011223344",
            full_name="Detective One",
        )
        self.register_url = "/api/v1/identity/auth/register/"
        self.login_url = "/api/v1/identity/auth/login/"
        self.logout_url = "/api/v1/identity/auth/logout/"
        self.me_url = "/api/v1/identity/auth/me/"

    def test_register_returns_token_credentials(self):
        payload = {
            "username": "officer02",
            "email": "officer02@example.com",
            "phone": "09120000002",
            "national_id": "9911223344",
            "full_name": "Officer Two",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["token_type"], "Token")
        self.assertIn("access_token", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["username"], "officer02")

    def test_register_duplicate_identifier_returns_validation_error(self):
        payload = {
            "username": "detective01",
            "email": "detective01@example.com",
            "phone": "09120000001",
            "national_id": "0011223344",
            "full_name": "Duplicate User",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("details", response.data["error"])

    def test_login_with_username_returns_token_credentials(self):
        response = self.client.post(
            self.login_url,
            {"identifier": "detective01", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["token_type"], "Token")
        self.assertIn("access_token", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["email"], "detective01@example.com")

    def test_login_with_email_phone_and_national_id(self):
        for identifier in ["detective01@example.com", "09120000001", "0011223344"]:
            response = self.client.post(
                self.login_url,
                {"identifier": identifier, "password": "StrongPass123!"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data["success"])
            self.assertIn("access_token", response.data["data"])

    def test_login_invalid_credentials_returns_standard_error_contract(self):
        response = self.client.post(
            self.login_url,
            {"identifier": "detective01", "password": "wrong-pass"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "INVALID_CREDENTIALS")
        self.assertIn("message", response.data["error"])
        self.assertIn("details", response.data["error"])

    def test_login_validation_error_returns_standard_error_contract(self):
        response = self.client.post(
            self.login_url,
            {"identifier": "", "password": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("details", response.data["error"])

    def test_me_requires_token_and_returns_standard_error_contract(self):
        response = self.client.get(self.me_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "UNAUTHORIZED")
        self.assertIn("details", response.data["error"])

    def test_me_returns_authenticated_user(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get(self.me_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["username"], "detective01")

    def test_logout_deletes_current_user_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post(self.logout_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertFalse(Token.objects.filter(key=token.key).exists())
