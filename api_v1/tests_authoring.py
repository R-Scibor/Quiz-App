from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status


class AuthoringAuthTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user("author", password="p", is_staff=True)
        self.staff_token = Token.objects.create(user=self.staff)
        self.user = User.objects.create_user("learner", password="p", is_staff=False)
        self.user_token = Token.objects.create(user=self.user)

    def test_validate_anonymous_401(self):
        r = self.client.post("/api/v1/authoring/validate/", {"questions": []}, format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(r.data["error"], "AUTHENTICATION_FAILED")

    def test_validate_non_staff_403(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.user_token.key}")
        r = self.client.post("/api/v1/authoring/validate/", {"questions": []}, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(r.data["error"], "PERMISSION_DENIED")


class AuthoringValidateTests(APITestCase):
    def setUp(self):
        staff = User.objects.create_user("author", password="p", is_staff=True)
        token = Token.objects.create(user=staff)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_invalid_returns_200_with_errors(self):
        r = self.client.post(
            "/api/v1/authoring/validate/",
            {"category": "X", "scope": "Y", "questions": []},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertFalse(r.data["valid"])
        self.assertTrue(any(e["code"] == "EMPTY_QUESTIONS" for e in r.data["errors"]))

    def test_valid_returns_200(self):
        payload = {
            "category": "History",
            "scope": "Medieval Poland",
            "questions": [{
                "id": 1,
                "questionText": "Coronation year?",
                "type": "single-choice",
                "options": ["966", "1025"],
                "correctAnswers": [1],
            }],
        }
        r = self.client.post("/api/v1/authoring/validate/", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(r.data["valid"])
        self.assertEqual(r.data["errors"], [])

    def test_schema_contains_schema_version(self):
        r = self.client.get("/api/v1/authoring/schema/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["schema_version"], 1)
        self.assertIn("single-choice", r.data["examples"])

    def test_instructions_returns_markdown(self):
        r = self.client.get("/api/v1/authoring/instructions/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("markdown", r.data)
        self.assertIn("active recall", r.data["markdown"])
