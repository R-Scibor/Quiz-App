"""
Tests for Celery tasks and the CheckOpenAnswerView dispatch.

_parse_llm_json: pure unit tests — no DB, no network.
generate_ai_answer: router logic tested by patching per-pipeline functions.
CheckOpenAnswerView: dispatch tested by patching the Celery task.
"""
import json
import os
import unittest
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase
from rest_framework import status

from api_v1.models import PromptConfiguration, Test, Question


class ParseLlmJsonTestCase(unittest.TestCase):
    """Pure unit tests for api_v1.tasks._parse_llm_json."""

    def _parse(self, raw):
        from api_v1.tasks import _parse_llm_json
        return _parse_llm_json(raw)

    # -------------------------------------------------------------------------
    # Happy paths
    # -------------------------------------------------------------------------

    def test_valid_json_returns_dict(self):
        result = self._parse('{"score": 3, "feedback": "Good answer."}')
        self.assertEqual(result['score'], 3)
        self.assertEqual(result['feedback'], 'Good answer.')

    def test_strips_json_code_fence(self):
        raw = '```json\n{"score": 2, "feedback": "OK"}\n```'
        result = self._parse(raw)
        self.assertEqual(result['score'], 2)

    def test_strips_bare_code_fence(self):
        raw = '```\n{"score": 1, "feedback": "Partial"}\n```'
        result = self._parse(raw)
        self.assertEqual(result['score'], 1)

    def test_strips_leading_trailing_whitespace(self):
        raw = '  {"score": 0, "feedback": "Wrong"}  '
        result = self._parse(raw)
        self.assertEqual(result['score'], 0)

    def test_score_zero_is_valid(self):
        """score=0 must not be treated as falsy and raise an error."""
        result = self._parse('{"score": 0, "feedback": "No credit."}')
        self.assertEqual(result['score'], 0)

    def test_extra_fields_preserved(self):
        raw = '{"score": 4, "feedback": "Great.", "grading_method": "llm"}'
        result = self._parse(raw)
        self.assertEqual(result.get('grading_method'), 'llm')

    def test_fence_with_trailing_whitespace_after_closing(self):
        raw = '```json\n{"score": 5, "feedback": "Perfect"}\n```  '
        result = self._parse(raw)
        self.assertEqual(result['score'], 5)

    # -------------------------------------------------------------------------
    # Error paths
    # -------------------------------------------------------------------------

    def test_invalid_json_raises_value_error(self):
        with self.assertRaises(ValueError):
            self._parse('not json at all')

    def test_missing_score_key_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            self._parse('{"feedback": "Looks good"}')
        self.assertIn('score', str(ctx.exception))

    def test_missing_feedback_key_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            self._parse('{"score": 3}')
        self.assertIn('feedback', str(ctx.exception))

    def test_empty_string_raises_value_error(self):
        with self.assertRaises(ValueError):
            self._parse('')


class GenerateAiAnswerTaskTestCase(TestCase):
    """
    Tests for the generate_ai_answer Celery task routing logic.

    The task is tested synchronously (CELERY_TASK_ALWAYS_EAGER).
    Per-pipeline functions are patched so no LLM calls occur.
    """

    @classmethod
    def setUpTestData(cls):
        PromptConfiguration.objects.create(
            name='default',
            prompt_text='Q: {question_text}\nA: {user_answer}\nCriteria: {grading_criteria}',
            is_active=True,
        )

    def _call(self, question_type='open-text', force_llm=False, extra_env=None):
        from api_v1.tasks import generate_ai_answer
        env = {'GEMINI_API_KEY': 'fake-key'}
        if extra_env:
            env.update(extra_env)
        with patch.dict(os.environ, env, clear=False):
            return generate_ai_answer(
                user_answer='test answer',
                grading_criteria='test criteria',
                question_text='test question?',
                max_points=5,
                question_type=question_type,
                force_llm=force_llm,
            )

    # -------------------------------------------------------------------------
    # API key guard
    # -------------------------------------------------------------------------

    def test_missing_gemini_api_key_returns_error_dict(self):
        """If GEMINI_API_KEY is absent the task returns an error dict (does not raise).

        We force LLM_PROVIDER=gemini and clear all other env vars so that
        Vertex AI credentials (which may be set in Docker) cannot bypass the
        GEMINI_API_KEY check.
        """
        from api_v1.tasks import generate_ai_answer
        # clear=True replaces the entire os.environ; only LLM_PROVIDER survives.
        # GEMINI_API_KEY is absent, so generate_ai_answer must return an error dict.
        with patch.dict(os.environ, {'LLM_PROVIDER': 'gemini'}, clear=True):
            result = generate_ai_answer(
                user_answer='x', grading_criteria='y', question_text='z',
                max_points=1, question_type='open-text', force_llm=False,
            )
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'API_KEY_MISSING')

    # -------------------------------------------------------------------------
    # Routing
    # -------------------------------------------------------------------------

    @patch('api_v1.tasks.grade_open_text')
    def test_open_text_routes_to_grade_open_text(self, mock_fn):
        mock_fn.return_value = {'score': 3, 'feedback': 'ok', 'grading_method': 'vector_pass',
                                'max_points': 5, 'vector_score': 0.9, 'latency_ms': 10}
        self._call(question_type='open-text')
        mock_fn.assert_called_once()

    @patch('api_v1.tasks.grade_open_text')
    def test_open_ended_legacy_routes_to_grade_open_text(self, mock_fn):
        mock_fn.return_value = {'score': 3, 'feedback': 'ok', 'grading_method': 'llm',
                                'max_points': 5, 'vector_score': None, 'latency_ms': 10}
        self._call(question_type='open-ended')
        mock_fn.assert_called_once()

    @patch('api_v1.tasks.grade_open_cli')
    def test_open_cli_routes_to_grade_open_cli(self, mock_fn):
        mock_fn.return_value = {'score': 3, 'feedback': 'ok', 'grading_method': 'regex_pass',
                                'max_points': 5, 'vector_score': None, 'latency_ms': 5}
        self._call(question_type='open-cli')
        mock_fn.assert_called_once()

    @patch('api_v1.tasks.grade_open_code')
    def test_open_code_routes_to_grade_open_code(self, mock_fn):
        mock_fn.return_value = {'score': 4, 'feedback': 'good code', 'grading_method': 'llm',
                                'max_points': 5, 'vector_score': None, 'latency_ms': 200}
        self._call(question_type='open-code')
        mock_fn.assert_called_once()

    @patch('api_v1.tasks.grade_open_text')
    def test_unknown_type_falls_back_to_open_text(self, mock_fn):
        """Unrecognised question_type should fall through to the open-text pipeline."""
        mock_fn.return_value = {'score': 2, 'feedback': 'fallback', 'grading_method': 'llm',
                                'max_points': 5, 'vector_score': None, 'latency_ms': 50}
        self._call(question_type='open-unknown-xyz')
        mock_fn.assert_called_once()


class CheckOpenAnswerViewDispatchTestCase(APITestCase):
    """Tests that CheckOpenAnswerView correctly dispatches to the Celery task."""

    URL = '/api/v1/check_answer/'

    @classmethod
    def setUpTestData(cls):
        cls.test = Test.objects.create(title="Grading contract test")
        cls.open_q = Question.objects.create(
            test=cls.test,
            text="What does DNS do?",
            question_type=Question.OPEN_TEXT,
            grading_criteria="Must mention name-to-IP mapping.",
            max_points=3,
        )
        cls.closed_q = Question.objects.create(
            test=cls.test,
            text="DNS stands for?",
            question_type=Question.SINGLE_CHOICE,
            max_points=None,
        )

    @property
    def valid_payload(self):
        return {
            'question': str(self.open_q.id),
            'userAnswer': 'DNS maps names to IP addresses.',
            'forceAI': False,
        }

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def test_missing_question_returns_400_incomplete_data(self):
        payload = {k: v for k, v in self.valid_payload.items() if k != 'question'}
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'INCOMPLETE_DATA')

    def test_missing_userAnswer_returns_400_incomplete_data(self):
        payload = {k: v for k, v in self.valid_payload.items() if k != 'userAnswer'}
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'INCOMPLETE_DATA')

    def test_unknown_question_returns_404(self):
        payload = {
            **self.valid_payload,
            'question': '00000000-0000-0000-0000-000000000000',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'QUESTION_NOT_FOUND')

    def test_closed_question_returns_400_invalid_type(self):
        payload = {
            **self.valid_payload,
            'question': str(self.closed_q.id),
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'INVALID_QUESTION_TYPE')

    def test_open_question_missing_rubric_returns_400(self):
        incomplete_q = Question.objects.create(
            test=self.test,
            text="What is a CNAME?",
            question_type=Question.OPEN_TEXT,
            grading_criteria=None,
            max_points=None,
        )
        payload = {
            **self.valid_payload,
            'question': str(incomplete_q.id),
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'MISSING_GRADING_CONFIG')

    # -------------------------------------------------------------------------
    # Dispatch
    # -------------------------------------------------------------------------

    @patch('api_v1.views.generate_ai_answer')
    def test_valid_payload_returns_202_with_task_id(self, mock_task):
        mock_delay_result = MagicMock()
        mock_delay_result.id = 'fake-task-id-abc'
        mock_task.delay.return_value = mock_delay_result

        response = self.client.post(self.URL, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['task_id'], 'fake-task-id-abc')

    @patch('api_v1.views.generate_ai_answer')
    def test_delay_uses_database_fields_not_client_overrides(self, mock_task):
        mock_delay_result = MagicMock()
        mock_delay_result.id = 'task-123'
        mock_task.delay.return_value = mock_delay_result

        payload = {
            **self.valid_payload,
            'gradingCriteria': 'CLIENT OVERRIDE — ignore this rubric.',
            'maxPoints': 99,
            'questionType': 'open-code',
            'questionText': 'CLIENT OVERRIDE — ignore this prompt.',
            'forceAI': True,
        }
        self.client.post(self.URL, payload, format='json')
        mock_task.delay.assert_called_once_with(
            'DNS maps names to IP addresses.',
            self.open_q.grading_criteria,
            self.open_q.text,
            self.open_q.max_points,
            self.open_q.question_type,
            True,
        )
