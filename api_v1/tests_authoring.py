from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status

from api_v1.quiz_import import import_quiz


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

    def test_validate_invalid_token_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token not-a-real-token")
        r = self.client.post("/api/v1/authoring/validate/", {"questions": []}, format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(r.data["error"], "AUTHENTICATION_FAILED")



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


class AuthoringReadTests(APITestCase):
    def setUp(self):
        staff = User.objects.create_user("author", password="p", is_staff=True)
        token = Token.objects.create(user=staff)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        result = import_quiz({
            "category": "History",
            "scope": "Medieval Poland",
            "version": "1.0",
            "questions": [{
                "id": 1,
                "questionText": "Coronation year?",
                "type": "single-choice",
                "options": ["966", "1025"],
                "correctAnswers": [1],
            }],
        })
        self.test_id = result["test"]["test_id"]
        self.question_id = result["quiz"]["questions"][0]["question_id"]

    def test_list_tests(self):
        r = self.client.get("/api/v1/authoring/tests/")
        self.assertEqual(r.status_code, 200)
        row = r.data[0]
        self.assertEqual(row["test_id"], self.test_id)
        self.assertEqual(row["scope"], "Medieval Poland")
        self.assertEqual(row["category"], "History")
        self.assertEqual(row["question_counts"]["total"], 1)

    def test_export(self):
        r = self.client.get(f"/api/v1/authoring/tests/{self.test_id}/export/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["questions"][0]["question_id"], self.question_id)
        self.assertEqual(r.data["questions"][0]["id"], 1)

    def test_get_question(self):
        r = self.client.get(
            f"/api/v1/authoring/tests/{self.test_id}/questions/{self.question_id}/"
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["questionText"], "Coronation year?")

    def test_export_404(self):
        r = self.client.get("/api/v1/authoring/tests/00000000-0000-4000-8000-000000000000/export/")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.data["error"], "TEST_NOT_FOUND")
