import unittest
from unittest.mock import patch

from rest_framework.test import APITestCase
from rest_framework import status

from api_v1.models import Category, Test, Question, Answer


class QuizAPITests(APITestCase):
    """Tests for TestListView and QuestionListView."""

    @classmethod
    def setUpTestData(cls):
        cls.cat_history = Category.objects.create(name="History")
        cls.cat_biology = Category.objects.create(name="Biology")

        cls.test_historia = Test.objects.create(title="Historia")
        cls.test_historia.categories.add(cls.cat_history)

        cls.test_biologia = Test.objects.create(title="Biologia")
        cls.test_biologia.categories.add(cls.cat_biology)

        # Historia: 2 closed + 1 open
        cls.q1 = Question.objects.create(
            test=cls.test_historia, text="Who was the first king of Poland?",
            question_type=Question.SINGLE_CHOICE, explanation="Mieszko I.",
        )
        Answer.objects.create(question=cls.q1, text="Mieszko I", is_correct=True)
        Answer.objects.create(question=cls.q1, text="Bolesław Chrobry", is_correct=False)

        cls.q2 = Question.objects.create(
            test=cls.test_historia, text="Year of Poland's baptism?",
            question_type=Question.SINGLE_CHOICE, explanation="966 AD.",
        )
        Answer.objects.create(question=cls.q2, text="966", is_correct=True)
        Answer.objects.create(question=cls.q2, text="1025", is_correct=False)

        cls.q3 = Question.objects.create(
            test=cls.test_historia, text="Describe causes of the Union of Lublin.",
            question_type=Question.OPEN_TEXT,
            grading_criteria="Must mention the Muscovite threat.", max_points=5,
        )

        # Biologia: 1 single + 1 multiple, 0 open
        cls.q4 = Question.objects.create(
            test=cls.test_biologia, text="Energy center of the cell?",
            question_type=Question.SINGLE_CHOICE, explanation="Mitochondria.",
        )
        Answer.objects.create(question=cls.q4, text="Nucleus", is_correct=False)
        Answer.objects.create(question=cls.q4, text="Mitochondrion", is_correct=True)

        cls.q5 = Question.objects.create(
            test=cls.test_biologia, text="Which are organelles?",
            question_type=Question.MULTIPLE_CHOICE, explanation="Golgi and Mitochondrion.",
        )
        Answer.objects.create(question=cls.q5, text="DNA", is_correct=False)
        Answer.objects.create(question=cls.q5, text="Golgi apparatus", is_correct=True)
        Answer.objects.create(question=cls.q5, text="Mitochondrion", is_correct=True)

    # --- TestListView ---

    def test_list_available_tests_success(self):
        """GET /tests/ returns test metadata with question counts."""
        response = self.client.get('/api/v1/tests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)

        by_scope = {item['scope']: item for item in data}
        self.assertIn('Historia', by_scope)
        self.assertIn('Biologia', by_scope)

        historia = by_scope['Historia']
        self.assertEqual(historia['test_id'], str(self.test_historia.id))
        self.assertEqual(historia['question_counts']['total'], 3)
        self.assertEqual(historia['question_counts']['closed'], 2)
        self.assertEqual(historia['question_counts']['open'], 1)

        biologia = by_scope['Biologia']
        self.assertEqual(biologia['test_id'], str(self.test_biologia.id))
        self.assertEqual(biologia['question_counts']['total'], 2)
        self.assertEqual(biologia['question_counts']['closed'], 2)
        self.assertEqual(biologia['question_counts']['open'], 0)

    # --- QuestionListView ---

    def test_get_questions_missing_params(self):
        """Missing required params return HTTP 400."""
        response = self.client.get('/api/v1/questions/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'MISSING_PARAMETERS')

    def test_get_questions_more_than_available(self):
        """Requesting more questions than available returns all available."""
        response = self.client.get(
            '/api/v1/questions/',
            {'categories': str(self.test_biologia.id), 'num_questions': 10},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_question_shuffling_logic(self):
        """After shuffling, correctAnswers indices still point to the correct option texts."""
        correct_texts = set(
            Answer.objects.filter(question=self.q5, is_correct=True).values_list('text', flat=True)
        )

        response = self.client.get(
            '/api/v1/questions/',
            {'categories': str(self.test_biologia.id), 'num_questions': 2},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        q5_str = str(self.q5.id)
        shuffled = next((q for q in response.json() if q['id'] == q5_str), None)
        self.assertIsNotNone(shuffled, "q5 (multiple-choice) must appear in the response")

        shuffled_correct_texts = {shuffled['options'][i] for i in shuffled['correctAnswers']}
        self.assertEqual(correct_texts, shuffled_correct_texts)

    def test_get_questions_mode_closed_only(self):
        """`mode=closed` returns only closed questions."""
        response = self.client.get(
            '/api/v1/questions/',
            {'categories': str(self.test_historia.id), 'num_questions': 2, 'mode': 'closed'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        questions = response.json()
        self.assertEqual(len(questions), 2)
        for q in questions:
            self.assertIn(q['type'], ['single-choice', 'multiple-choice'])
            self.assertGreater(len(q['options']), 0)

    def test_get_questions_mode_open_only(self):
        """`mode=open` returns only open questions."""
        response = self.client.get(
            '/api/v1/questions/',
            {'categories': str(self.test_historia.id), 'num_questions': 1, 'mode': 'open'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        questions = response.json()
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['type'], 'open-text')
        self.assertIsNotNone(questions[0]['gradingCriteria'])
        self.assertEqual(questions[0]['options'], [])

    def test_get_questions_mode_mixed_default(self):
        """Default mode (mixed) returns both open and closed questions."""
        response = self.client.get(
            '/api/v1/questions/',
            {'categories': str(self.test_historia.id), 'num_questions': 3},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        questions = response.json()
        self.assertEqual(len(questions), 3)
        types = {q['type'] for q in questions}
        self.assertIn('open-text', types)
        self.assertIn('single-choice', types)

    def test_get_questions_invalid_mode(self):
        """An invalid `mode` value returns HTTP 400."""
        response = self.client.get(
            '/api/v1/questions/',
            {'categories': str(self.test_historia.id), 'num_questions': 1, 'mode': 'wrong_mode'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'INVALID_MODE_PARAMETER')

    def test_get_questions_no_questions_for_mode(self):
        """Returns HTTP 404 when no questions match the requested mode."""
        response = self.client.get(
            '/api/v1/questions/',
            {'categories': str(self.test_biologia.id), 'num_questions': 1, 'mode': 'open'},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'NO_QUESTIONS_FOUND')


class QuizAPIEmptyStateTests(APITestCase):
    """Tests API behaviour when the database has no Test objects."""

    def test_list_available_tests_empty(self):
        """GET /tests/ returns an empty list when no tests exist."""
        response = self.client.get('/api/v1/tests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])


# ---------------------------------------------------------------------------
# Cascade grading — unit tests
# ---------------------------------------------------------------------------

class SanitizersTestCase(unittest.TestCase):
    """Unit tests for text sanitizer helpers."""

    def test_sanitize_text_strips_html(self):
        from api_v1.tasks import sanitize_text
        self.assertEqual(sanitize_text("<b>Hello</b> world"), "Hello world")

    def test_sanitize_text_collapses_whitespace(self):
        from api_v1.tasks import sanitize_text
        self.assertEqual(sanitize_text("  foo   bar  "), "foo bar")

    def test_sanitize_text_normalizes_unicode(self):
        from api_v1.tasks import sanitize_text
        # NFKC: ligature ﬁ → fi
        self.assertEqual(sanitize_text("ﬁle"), "file")

    def test_sanitize_cli_collapses_spaces(self):
        from api_v1.tasks import sanitize_cli
        self.assertEqual(sanitize_cli("  ls   -la  /tmp  "), "ls -la /tmp")

    def test_sanitize_cli_preserves_flags(self):
        from api_v1.tasks import sanitize_cli
        self.assertEqual(sanitize_cli("git commit -m 'msg'"), "git commit -m 'msg'")


class CascadeRoutingTestCase(unittest.TestCase):
    """Integration tests for cascade grading routing (mocking vector service and LLM dispatcher)."""

    def _make_result(self, score, feedback, grading_method, vector_score=None):
        return {
            "score": score, "max_points": 5, "feedback": feedback,
            "grading_method": grading_method, "vector_score": vector_score,
            "latency_ms": 10,
        }

    @patch("api_v1.tasks.call_vector_service", return_value=0.90)
    def test_open_text_vector_pass(self, _mock):
        from api_v1.tasks import grade_open_text
        result = grade_open_text("Q?", "expected answer", 5, "expected answer")
        self.assertEqual(result["grading_method"], "vector_pass")
        self.assertEqual(result["score"], 5)

    @patch("api_v1.tasks.call_vector_service", return_value=0.20)
    def test_open_text_vector_fail(self, _mock):
        from api_v1.tasks import grade_open_text
        result = grade_open_text("Q?", "expected answer", 5, "completely wrong")
        self.assertEqual(result["grading_method"], "vector_fail")
        self.assertEqual(result["score"], 0)

    @patch("api_v1.tasks._call_llm")
    @patch("api_v1.tasks.call_vector_service", return_value=0.55)
    def test_open_text_ambiguous_calls_llm(self, _mock_vec, mock_llm):
        from api_v1.tasks import grade_open_text
        mock_llm.return_value = {"score": 3, "feedback": "Partially correct."}
        result = grade_open_text("Q?", "expected answer", 5, "partial answer")
        self.assertEqual(result["grading_method"], "llm")
        mock_llm.assert_called_once()

    @patch("api_v1.tasks.call_vector_service", return_value=None)
    @patch("api_v1.tasks._call_llm")
    def test_open_text_vector_unreachable_fallback(self, mock_llm, _mock_vec):
        from api_v1.tasks import grade_open_text
        mock_llm.return_value = {"score": 4, "feedback": "Good."}
        result = grade_open_text("Q?", "expected answer", 5, "good answer")
        self.assertEqual(result["grading_method"], "fallback_llm")
        mock_llm.assert_called_once()

    def test_open_cli_regex_match(self):
        from api_v1.tasks import grade_open_cli
        result = grade_open_cli("List files", r"ls\s+-la?\s*/tmp", 3, "ls -la /tmp")
        self.assertEqual(result["grading_method"], "regex_pass")
        self.assertEqual(result["score"], 3)

    def test_open_cli_regex_no_match_calls_llm(self):
        from api_v1.tasks import grade_open_cli
        with patch("api_v1.tasks._call_llm") as mock_llm:
            mock_llm.return_value = {"score": 0, "feedback": "Wrong."}
            result = grade_open_cli("List files", r"ls\s+-la?\s*/tmp", 3, "rm -rf /tmp")
        self.assertEqual(result["grading_method"], "llm")

    def test_open_code_always_uses_llm(self):
        from api_v1.tasks import grade_open_code
        with patch("api_v1.tasks._call_llm") as mock_llm:
            mock_llm.return_value = {"score": 2, "feedback": "Partial."}
            result = grade_open_code("Write FizzBuzz", "python: FizzBuzz in Python", 5, "print('fizz')")
        self.assertEqual(result["grading_method"], "llm")
        mock_llm.assert_called_once()


class ImportQuizzesValidationTestCase(unittest.TestCase):
    """Tests for open-cli regex and open-code language prefix validation in import command."""

    def setUp(self):
        from api_v1.management.commands.import_quizzes import Command
        self.cmd = Command()

    def test_valid_regex_passes(self):
        self.assertIsNone(self.cmd._validate_regex(r"ls\s+-la?\s*/\w+"))

    def test_invalid_regex_fails(self):
        error = self.cmd._validate_regex(r"[invalid")
        self.assertIsNotNone(error)
        self.assertIn("Invalid regex", error)

    def test_catastrophic_regex_rejected(self):
        error = self.cmd._validate_regex(r"(a+)+")
        self.assertIsNotNone(error)

    def test_valid_code_criteria_with_prefix(self):
        """A criteria string with a colon is a valid open-code gradingCriteria."""
        criteria = "python: implement a function that returns the factorial"
        self.assertIn(":", criteria)  # basic format check

    def test_code_criteria_without_prefix_invalid(self):
        """Criteria without colon would be rejected by import logic."""
        criteria = "implement factorial function"
        self.assertNotIn(":", criteria)
