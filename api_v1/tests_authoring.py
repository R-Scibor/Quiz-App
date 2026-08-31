from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status

from api_v1.models import Test
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

    def test_schema_accepts_export_documents(self):
        r = self.client.get("/api/v1/authoring/schema/")
        schema = r.data["json_schema"]
        self.assertTrue(
            schema.get("additionalProperties") is True or "test_id" in schema["properties"]
        )
        test_id = schema["properties"].get("test_id", {})
        self.assertEqual(test_id.get("type"), "string")
        question = schema["$defs"]["question"]
        self.assertNotIn("id", question.get("required", []))
        id_schema = question["properties"]["id"]
        id_types = id_schema.get("type")
        if isinstance(id_types, list):
            self.assertIn("null", id_types)
            self.assertIn("integer", id_types)
        else:
            self.assertEqual(id_schema.get("type"), ["integer", "null"])
        self.assertIn("question_id", question["properties"])
        self.assertEqual(question["properties"]["question_id"].get("type"), "string")

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


class AuthoringPatchTests(APITestCase):
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

    def test_patch_scope_and_version(self):
        r = self.client.patch(
            f"/api/v1/authoring/tests/{self.test_id}/",
            {"scope": "Early Piasts", "version": "1.1"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["scope"], "Early Piasts")
        self.assertEqual(r.data["version"], "1.1")
        self.assertEqual(len(r.data["questions"]), 1)
        self.assertEqual(r.data["questions"][0]["question_id"], self.question_id)

    def test_patch_category(self):
        r = self.client.patch(
            f"/api/v1/authoring/tests/{self.test_id}/",
            {"category": "Polish History"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["category"], "Polish History")

    def test_patch_null_scope_400(self):
        r = self.client.patch(
            f"/api/v1/authoring/tests/{self.test_id}/",
            {"scope": None},
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"], "VALIDATION_FAILED")
        self.assertEqual(Test.objects.get(pk=self.test_id).title, "Medieval Poland")

    def test_patch_non_string_category_400(self):
        r = self.client.patch(
            f"/api/v1/authoring/tests/{self.test_id}/",
            {"category": 1},
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"], "VALIDATION_FAILED")


class AuthoringImportTests(APITestCase):
    def setUp(self):
        staff = User.objects.create_user("author", password="p", is_staff=True)
        token = Token.objects.create(user=staff)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        self.payload = {
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
        }

    def test_import_creates(self):
        r = self.client.post("/api/v1/authoring/import/", self.payload, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["applied"])
        self.assertEqual(r.data["quiz"]["scope"], "Medieval Poland")

    def test_import_invalid_400(self):
        r = self.client.post(
            "/api/v1/authoring/import/",
            {"category": "X", "scope": "Y", "questions": []},
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"], "VALIDATION_FAILED")
        self.assertEqual(Test.objects.count(), 0)

    def test_import_null_scope_400(self):
        payload = {
            "category": "X",
            "scope": None,
            "questions": [{
                "id": 1,
                "questionText": "Coronation year?",
                "type": "single-choice",
                "options": ["966", "1025"],
                "correctAnswers": [1],
            }],
        }
        r = self.client.post("/api/v1/authoring/import/", payload, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"], "VALIDATION_FAILED")
        self.assertEqual(Test.objects.count(), 0)

    def test_import_non_integer_id_400(self):
        self.payload["questions"][0]["id"] = "abc"
        r = self.client.post("/api/v1/authoring/import/", self.payload, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"], "VALIDATION_FAILED")
        self.assertEqual(Test.objects.count(), 0)

    def test_dry_run_query_param(self):
        r = self.client.post("/api/v1/authoring/import/?dry_run=true", self.payload, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["applied"])
        self.assertEqual(Test.objects.count(), 0)

    def test_unknown_test_id_404(self):
        self.payload["test_id"] = "00000000-0000-4000-8000-000000000000"
        r = self.client.post("/api/v1/authoring/import/", self.payload, format="json")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.data["error"], "TEST_NOT_FOUND")
