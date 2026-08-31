from django.test import SimpleTestCase

from api_v1.quiz_validation import validate_quiz


def _closed(qid=1, **over):
    q = {
        "id": qid,
        "questionText": "What year?",
        "type": "single-choice",
        "options": ["966", "1000", "1025", "1138"],
        "correctAnswers": [2],
        "explanation": "1025",
        "tags": ["dates"],
        "image": "",
    }
    q.update(over)
    return q


def _quiz(*questions, **over):
    data = {
        "category": "History",
        "scope": "Medieval Poland",
        "version": "1.0",
        "questions": list(questions),
    }
    data.update(over)
    return data


class ValidateQuizTests(SimpleTestCase):
    def test_valid_closed_quiz_returns_no_issues(self):
        self.assertEqual(validate_quiz(_quiz(_closed())), [])

    def test_missing_scope_is_missing_field(self):
        data = _quiz(_closed())
        del data["scope"]
        issues = validate_quiz(data)
        codes = {i["code"] for i in issues}
        self.assertIn("MISSING_FIELD", codes)
        paths = {i["path"] for i in issues}
        self.assertIn("scope", paths)

    def test_empty_questions_is_error(self):
        issues = validate_quiz(_quiz())
        self.assertTrue(any(i["code"] == "EMPTY_QUESTIONS" for i in issues))

    def test_unknown_type_is_error_not_warning(self):
        issues = validate_quiz(_quiz(_closed(type="true-false")))
        self.assertTrue(any(i["code"] == "INVALID_QUESTION_TYPE" for i in issues))
        self.assertTrue(any(i["path"] == "questions[0].type" for i in issues))

    def test_single_choice_requires_exactly_one_correct(self):
        issues = validate_quiz(_quiz(_closed(correctAnswers=[0, 1])))
        self.assertTrue(any(i["code"] == "INVALID_CORRECT_ANSWERS" for i in issues))

    def test_open_text_requires_grading_fields(self):
        q = {
            "id": 1,
            "questionText": "Explain DNS.",
            "type": "open-text",
            "tags": ["dns"],
        }
        issues = validate_quiz(_quiz(q))
        codes = {i["code"] for i in issues}
        self.assertIn("MISSING_GRADING_CONFIG", codes)

    def test_open_cli_invalid_regex(self):
        q = {
            "id": 1,
            "questionText": "List files",
            "type": "open-cli",
            "gradingCriteria": "(",
            "maxPoints": 1,
        }
        issues = validate_quiz(_quiz(q))
        self.assertTrue(any(i["code"] == "INVALID_REGEX" for i in issues))

    def test_open_code_requires_language_prefix(self):
        q = {
            "id": 1,
            "questionText": "Write a function",
            "type": "open-code",
            "gradingCriteria": "must return 42",
            "maxPoints": 3,
        }
        issues = validate_quiz(_quiz(q))
        self.assertTrue(any(i["code"] == "INVALID_CODE_CRITERIA" for i in issues))

    def test_duplicate_source_id(self):
        issues = validate_quiz(_quiz(_closed(1), _closed(1, questionText="Other?")))
        self.assertTrue(any(i["code"] == "DUPLICATE_SOURCE_ID" for i in issues))

    def test_legacy_open_ended_is_not_an_error(self):
        q = {
            "id": 1,
            "questionText": "Explain DNS.",
            "type": "open-ended",
            "gradingCriteria": "recursive lookup",
            "maxPoints": 3,
        }
        issues = validate_quiz(_quiz(q))
        self.assertEqual(issues, [])

    def test_issue_shape(self):
        data = _quiz(_closed())
        del data["category"]
        issues = validate_quiz(data)
        self.assertEqual(set(issues[0].keys()), {"path", "code", "message"})
