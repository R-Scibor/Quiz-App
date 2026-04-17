"""
Tests for authentication endpoints and session/attempt lifecycle.

Auth endpoints: /api/v1/auth/register/, /api/v1/auth/login/, /api/v1/auth/logout/
Session endpoints: /api/v1/sessions/start/, /api/v1/sessions/<pk>/complete/
Attempt endpoint: /api/v1/attempts/
"""
import uuid

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status

from api_v1.models import Test, Question, Answer, QuizSession, QuestionAttempt


class AuthViewsTestCase(APITestCase):
    REGISTER_URL = '/api/v1/auth/register/'
    LOGIN_URL = '/api/v1/auth/login/'
    LOGOUT_URL = '/api/v1/auth/logout/'
    STATS_URL = '/api/v1/stats/'

    def _register_and_login(self, username='testuser', password='securepass123'):
        """Helper: creates a user and returns their auth token string."""
        user = User.objects.create_user(username=username, password=password)
        token, _ = Token.objects.get_or_create(user=user)
        return user, token.key

    # -------------------------------------------------------------------------
    # Register
    # -------------------------------------------------------------------------

    def test_register_success_returns_201_with_token_and_username(self):
        payload = {'username': 'alice', 'password': 'hunter2x'}
        response = self.client.post(self.REGISTER_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'alice')

    def test_register_duplicate_username_returns_400(self):
        User.objects.create_user(username='bob', password='pass123')
        payload = {'username': 'bob', 'password': 'different_pass'}
        response = self.client.post(self.REGISTER_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password_returns_400(self):
        """Password shorter than 6 characters is rejected by RegisterSerializer."""
        payload = {'username': 'charlie', 'password': 'abc'}
        response = self.client.post(self.REGISTER_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # Login
    # -------------------------------------------------------------------------

    def test_login_success_returns_200_with_token(self):
        User.objects.create_user(username='diana', password='correctpass')
        payload = {'username': 'diana', 'password': 'correctpass'}
        response = self.client.post(self.LOGIN_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'diana')

    def test_login_wrong_password_returns_401(self):
        User.objects.create_user(username='eve', password='right_password')
        payload = {'username': 'eve', 'password': 'wrong_password'}
        response = self.client.post(self.LOGIN_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error'], 'INVALID_CREDENTIALS')

    def test_login_missing_fields_returns_400(self):
        """Sending neither username nor password returns MISSING_CREDENTIALS."""
        response = self.client.post(self.LOGIN_URL, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'MISSING_CREDENTIALS')

    def test_login_missing_password_returns_400(self):
        response = self.client.post(self.LOGIN_URL, {'username': 'frank'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'MISSING_CREDENTIALS')

    # -------------------------------------------------------------------------
    # Logout
    # -------------------------------------------------------------------------

    def test_logout_success_returns_204(self):
        _, token_key = self._register_and_login('grace', 'password1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token_key}')
        response = self.client.post(self.LOGOUT_URL)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_invalidates_token(self):
        """After logout, the same token should no longer authenticate."""
        _, token_key = self._register_and_login('henry', 'password2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token_key}')
        self.client.post(self.LOGOUT_URL)
        # Attempt to use the now-deleted token
        response = self.client.get(self.STATS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_token_returns_401(self):
        response = self.client.post(self.LOGOUT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_endpoint_without_token_returns_401(self):
        """Hitting a protected endpoint with no credentials returns 401."""
        response = self.client.get(self.STATS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SessionLifecycleTestCase(APITestCase):
    START_URL = '/api/v1/sessions/start/'

    @classmethod
    def setUpTestData(cls):
        cls.user_a = User.objects.create_user(username='user_a', password='pass_a')
        cls.token_a, _ = Token.objects.get_or_create(user=cls.user_a)

        cls.user_b = User.objects.create_user(username='user_b', password='pass_b')
        cls.token_b, _ = Token.objects.get_or_create(user=cls.user_b)

    def _complete_url(self, session_id):
        return f'/api/v1/sessions/{session_id}/complete/'

    # -------------------------------------------------------------------------
    # Session start
    # -------------------------------------------------------------------------

    def test_session_start_returns_201_with_session_id(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        response = self.client.post(self.START_URL, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('session_id', response.data)
        # Must be a valid UUID
        uuid.UUID(response.data['session_id'])

    def test_session_start_study_mode_persisted(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        response = self.client.post(self.START_URL, {'is_study_mode': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = QuizSession.objects.get(pk=response.data['session_id'])
        self.assertTrue(session.is_study_mode)

    def test_session_start_requires_auth(self):
        response = self.client.post(self.START_URL, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # Session complete
    # -------------------------------------------------------------------------

    def test_session_complete_returns_200_and_sets_completed_at(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        session = QuizSession.objects.create(user=self.user_a)

        response = self.client.post(
            self._complete_url(session.id),
            {'total_questions': 5, 'correct_count': 3, 'score_achieved': 3, 'score_possible': 5},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertIsNotNone(session.completed_at)
        self.assertEqual(session.total_questions, 5)
        self.assertEqual(session.correct_count, 3)

    def test_session_complete_wrong_user_returns_404(self):
        """User B cannot complete a session belonging to User A."""
        session = QuizSession.objects.create(user=self.user_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_b.key}')
        response = self.client.post(
            self._complete_url(session.id),
            {'total_questions': 1, 'correct_count': 1, 'score_achieved': 1, 'score_possible': 1},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_session_complete_nonexistent_session_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        fake_id = uuid.uuid4()
        response = self.client.post(
            self._complete_url(fake_id),
            {'total_questions': 1, 'correct_count': 1, 'score_achieved': 1, 'score_possible': 1},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AttemptCreateViewTestCase(APITestCase):
    ATTEMPTS_URL = '/api/v1/attempts/'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='attempt_user', password='pass123')
        cls.token, _ = Token.objects.get_or_create(user=cls.user)

        cls.test_obj = Test.objects.create(title='Attempt Test')
        cls.question = Question.objects.create(
            test=cls.test_obj,
            text='What is 2+2?',
            question_type=Question.SINGLE_CHOICE,
        )
        Answer.objects.create(question=cls.question, text='4', is_correct=True)
        Answer.objects.create(question=cls.question, text='5', is_correct=False)

        cls.question2 = Question.objects.create(
            test=cls.test_obj,
            text='Capital of France?',
            question_type=Question.SINGLE_CHOICE,
        )
        Answer.objects.create(question=cls.question2, text='Paris', is_correct=True)

    def setUp(self):
        self.session = QuizSession.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def _attempt_payload(self, question=None, extra=None):
        payload = {
            'question': str((question or self.question).id),
            'test': str(self.test_obj.id),
            'session': str(self.session.id),
            'is_correct': True,
            'points_awarded': 1,
            'time_spent_secs': 10,
        }
        if extra:
            payload.update(extra)
        return payload

    # -------------------------------------------------------------------------
    # Single attempt — no difficulty rating
    # -------------------------------------------------------------------------

    def test_single_attempt_without_rating_returns_201(self):
        response = self.client.post(self.ATTEMPTS_URL, self._attempt_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_single_attempt_without_rating_creates_db_record(self):
        self.client.post(self.ATTEMPTS_URL, self._attempt_payload(), format='json')
        attempt = QuestionAttempt.objects.get(user=self.user, question=self.question)
        self.assertTrue(attempt.is_correct)
        self.assertEqual(attempt.sr_interval, 1)
        self.assertAlmostEqual(attempt.sr_ease_factor, 2.5)
        self.assertIsNone(attempt.sr_next_review)
        self.assertEqual(attempt.sr_repetitions, 0)

    # -------------------------------------------------------------------------
    # Single attempt — with difficulty rating (triggers SM-2)
    # -------------------------------------------------------------------------

    def test_single_attempt_with_easy_rating_sets_sr_next_review(self):
        payload = self._attempt_payload(extra={'difficulty_rating': 'easy'})
        response = self.client.post(self.ATTEMPTS_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        attempt = QuestionAttempt.objects.get(user=self.user, question=self.question)
        self.assertIsNotNone(attempt.sr_next_review)
        self.assertGreaterEqual(attempt.sr_interval, 1)

    def test_second_attempt_with_easy_rating_uses_sm2_second_branch(self):
        """Second easy attempt: prev_reps=1 → SM-2 produces interval=6, reps=2."""
        # First attempt
        payload = self._attempt_payload(extra={'difficulty_rating': 'easy'})
        self.client.post(self.ATTEMPTS_URL, payload, format='json')

        # Second attempt (new session to avoid duplicate key issues)
        session2 = QuizSession.objects.create(user=self.user)
        payload2 = self._attempt_payload(extra={'difficulty_rating': 'easy'})
        payload2['session'] = str(session2.id)
        self.client.post(self.ATTEMPTS_URL, payload2, format='json')

        latest = QuestionAttempt.objects.filter(
            user=self.user, question=self.question
        ).order_by('-answered_at').first()
        self.assertEqual(latest.sr_repetitions, 2)
        self.assertEqual(latest.sr_interval, 6)

    # -------------------------------------------------------------------------
    # Batch attempts
    # -------------------------------------------------------------------------

    def test_batch_attempts_returns_201_and_creates_all_records(self):
        session2 = QuizSession.objects.create(user=self.user)
        payload = [
            self._attempt_payload(),
            {
                'question': str(self.question2.id),
                'test': str(self.test_obj.id),
                'session': str(session2.id),
                'is_correct': False,
                'points_awarded': 0,
                'time_spent_secs': 5,
            },
        ]
        response = self.client.post(self.ATTEMPTS_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            QuestionAttempt.objects.filter(user=self.user).count(), 2
        )

    # -------------------------------------------------------------------------
    # Validation errors
    # -------------------------------------------------------------------------

    def test_missing_is_correct_returns_400(self):
        payload = self._attempt_payload()
        del payload['is_correct']
        response = self.client.post(self.ATTEMPTS_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_attempts_requires_auth(self):
        self.client.credentials()
        response = self.client.post(self.ATTEMPTS_URL, self._attempt_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
