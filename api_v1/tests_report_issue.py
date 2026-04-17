"""
End-to-end tests for POST /api/v1/report_issue/.

Covers the ReportIssueView and ReportedIssueSerializer validation logic.
No authentication is required for this endpoint (intentionally public).
"""
from rest_framework.test import APITestCase
from rest_framework import status

from api_v1.models import Test, Question, Answer, ReportedIssue


class ReportIssueViewTestCase(APITestCase):
    URL = '/api/v1/report_issue/'

    @classmethod
    def setUpTestData(cls):
        cls.test_obj = Test.objects.create(title='Test Alpha')

        cls.open_q = Question.objects.create(
            test=cls.test_obj,
            text='Explain how DNS resolution works.',
            question_type=Question.OPEN_TEXT,
            grading_criteria='Must mention recursive/iterative lookup and authoritative nameservers.',
            max_points=5,
        )

        cls.closed_q = Question.objects.create(
            test=cls.test_obj,
            text='Which is the largest planet?',
            question_type=Question.SINGLE_CHOICE,
        )
        cls.answer_a = Answer.objects.create(
            question=cls.closed_q, text='Jupiter', is_correct=True
        )
        cls.answer_b = Answer.objects.create(
            question=cls.closed_q, text='Saturn', is_correct=False
        )

        cls.other_test = Test.objects.create(title='Unrelated Test')

    # -------------------------------------------------------------------------
    # Happy paths
    # -------------------------------------------------------------------------

    def test_valid_open_question_error(self):
        """QUESTION_ERROR for an open question with user_answer_open → 201."""
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
            'user_answer_open': 'DNS finds IP addresses.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_valid_closed_question_error(self):
        """QUESTION_ERROR for a closed question with user_answer_choices → 201."""
        payload = {
            'question': str(self.closed_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
            'user_answer_choices': ['Jupiter'],
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_valid_ai_grading_error(self):
        """AI_GRADING_ERROR for an open question with snapshot → 201."""
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'AI_GRADING_ERROR',
            'user_answer_open': 'DNS finds IP addresses.',
            'ai_feedback_snapshot': '{"score": 2, "feedback": "Partial credit."}',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_description_is_optional(self):
        """Omitting description is valid → 201."""
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
            'user_answer_open': 'Some answer.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_created_issue_has_new_status(self):
        """Successfully created issues must have status='NEW' in the database."""
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
            'user_answer_open': 'DNS does name resolution.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        issue = ReportedIssue.objects.get(question=self.open_q, test=self.test_obj)
        self.assertEqual(issue.status, 'NEW')

    def test_no_authentication_required(self):
        """
        The endpoint is publicly accessible — no auth token needed.
        NOTE: This is intentional but means there is no rate-limiting beyond
        Django's ScopedRateThrottle on other views. A future improvement could
        add throttling here to prevent spam submissions.
        """
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
            'user_answer_open': 'Anonymous report.',
        }
        # Ensure no credentials are set
        self.client.credentials()
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # -------------------------------------------------------------------------
    # Serializer validation — AI grading error
    # -------------------------------------------------------------------------

    def test_ai_grading_error_missing_snapshot_returns_400(self):
        """AI_GRADING_ERROR without ai_feedback_snapshot → 400."""
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'AI_GRADING_ERROR',
            'user_answer_open': 'My answer.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ai_feedback_snapshot', response.data)

    # -------------------------------------------------------------------------
    # Serializer validation — question-test relationship
    # -------------------------------------------------------------------------

    def test_question_not_belonging_to_test_returns_400(self):
        """question from one test submitted with a different test ID → 400."""
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.other_test.id),  # wrong test
            'issue_type': 'QUESTION_ERROR',
            'user_answer_open': 'Some answer.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # Serializer validation — open question answer requirements
    # -------------------------------------------------------------------------

    def test_open_question_missing_user_answer_open_returns_400(self):
        """Open question without user_answer_open → 400."""
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_answer_open', response.data)

    def test_open_question_with_choices_returns_400(self):
        """Providing user_answer_choices for an open question → 400.
        Both fields are sent so validation passes the 'open required' check
        and reaches the 'choices not allowed' check."""
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
            'user_answer_open': 'My text answer.',
            'user_answer_choices': ['choice A'],
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_answer_choices', response.data)

    # -------------------------------------------------------------------------
    # Serializer validation — closed question answer requirements
    # -------------------------------------------------------------------------

    def test_closed_question_missing_user_answer_choices_returns_400(self):
        """Closed question without user_answer_choices → 400."""
        payload = {
            'question': str(self.closed_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_answer_choices', response.data)

    def test_closed_question_with_open_answer_returns_400(self):
        """Providing user_answer_open for a closed question → 400.
        Both fields are sent so validation passes the 'choices required' check
        and reaches the 'open answer not allowed' check."""
        payload = {
            'question': str(self.closed_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
            'user_answer_choices': ['Jupiter'],
            'user_answer_open': 'Some text.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_answer_open', response.data)

    # -------------------------------------------------------------------------
    # Serializer validation — missing required fields
    # -------------------------------------------------------------------------

    def test_missing_question_returns_400(self):
        payload = {
            'test': str(self.test_obj.id),
            'issue_type': 'QUESTION_ERROR',
            'user_answer_open': 'Answer.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_test_returns_400(self):
        payload = {
            'question': str(self.open_q.id),
            'issue_type': 'QUESTION_ERROR',
            'user_answer_open': 'Answer.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_issue_type_returns_400(self):
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'user_answer_open': 'Answer.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_issue_type_returns_400(self):
        """Unrecognised issue_type value → 400."""
        payload = {
            'question': str(self.open_q.id),
            'test': str(self.test_obj.id),
            'issue_type': 'MADE_UP_TYPE',
            'user_answer_open': 'Answer.',
        }
        response = self.client.post(self.URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
