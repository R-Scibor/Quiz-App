"""
Tests for Study Mode queue and stats.

Covers SM-2 due cards, unscheduled misses (struggling), new cards from
studied tests, leftover-slot fill, and stats matching the queue builder.
"""
from datetime import date, timedelta

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status

from api_v1.models import Test, Question, Answer, QuizSession, QuestionAttempt


class StudyModeTestCase(APITestCase):
    QUEUE_URL = '/api/v1/study/queue/'
    STATS_URL = '/api/v1/study/stats/'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='student', password='pass123')
        cls.token, _ = Token.objects.get_or_create(user=cls.user)
        cls.other = User.objects.create_user(username='other', password='pass123')

        cls.test_a = Test.objects.create(title='Topic A')
        cls.test_b = Test.objects.create(title='Topic B')
        cls.test_unseen = Test.objects.create(title='Never studied')

        cls.questions_a = [
            cls._make_question(cls.test_a, f'A question {i}')
            for i in range(6)
        ]
        cls.questions_b = [
            cls._make_question(cls.test_b, f'B question {i}')
            for i in range(3)
        ]
        cls.questions_unseen = [
            cls._make_question(cls.test_unseen, f'Unseen {i}')
            for i in range(2)
        ]

    @staticmethod
    def _make_question(test, text):
        q = Question.objects.create(
            test=test, text=text, question_type=Question.SINGLE_CHOICE,
        )
        Answer.objects.create(question=q, text='yes', is_correct=True)
        Answer.objects.create(question=q, text='no', is_correct=False)
        return q

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.session = QuizSession.objects.create(user=self.user)

    def _attempt(self, question, *, is_correct=True, rating=None,
                 next_review=None, reps=0, interval=1, ease=2.5, session=None):
        return QuestionAttempt.objects.create(
            user=self.user,
            question=question,
            test=question.test,
            session=session or self.session,
            is_correct=is_correct,
            points_awarded=1 if is_correct else 0,
            difficulty_rating=rating,
            sr_next_review=next_review,
            sr_repetitions=reps,
            sr_interval=interval,
            sr_ease_factor=ease,
        )

    def test_queue_requires_auth(self):
        self.client.credentials()
        response = self.client.get(self.QUEUE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_stats_requires_auth(self):
        self.client.credentials()
        response = self.client.get(self.STATS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_due_cards_are_included(self):
        today = date.today()
        due_q = self.questions_a[0]
        future_q = self.questions_a[1]
        self._attempt(due_q, rating='easy', next_review=today, reps=1)
        self._attempt(future_q, rating='easy', next_review=today + timedelta(days=6), reps=2, interval=6)

        response = self.client.get(self.QUEUE_URL, {'limit': 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data['questions']}
        self.assertIn(str(due_q.id), ids)
        self.assertNotIn(str(future_q.id), ids)

    def test_scheduled_incorrect_is_not_struggling(self):
        """Wrong + already scheduled for tomorrow is not a struggling card."""
        tomorrow = date.today() + timedelta(days=1)
        q = self.questions_a[0]
        self._attempt(q, is_correct=False, rating='hard', next_review=tomorrow, reps=0)

        stats = self.client.get(self.STATS_URL).data
        self.assertEqual(stats['due_count'], 0)
        self.assertEqual(stats['struggling_count'], 0)

        queue_ids = {item['id'] for item in self.client.get(self.QUEUE_URL).data['questions']}
        self.assertNotIn(str(q.id), queue_ids)

    def test_unscheduled_incorrect_is_struggling(self):
        q = self.questions_a[0]
        self._attempt(q, is_correct=False, rating=None, next_review=None)

        stats = self.client.get(self.STATS_URL).data
        self.assertEqual(stats['struggling_count'], 1)

        queue_ids = {item['id'] for item in self.client.get(self.QUEUE_URL).data['questions']}
        self.assertIn(str(q.id), queue_ids)

    def test_new_questions_only_from_studied_tests(self):
        self._attempt(self.questions_a[0], rating='easy', next_review=date.today(), reps=1)

        response = self.client.get(self.QUEUE_URL, {'limit': 50})
        ids = {item['id'] for item in response.data['questions']}
        unseen_ids = {str(q.id) for q in self.questions_unseen}
        self.assertTrue(unseen_ids.isdisjoint(ids))
        # Remaining Topic A questions should be eligible as new.
        self.assertIn(str(self.questions_a[1].id), ids)

    def test_other_users_attempts_do_not_affect_queue(self):
        other_session = QuizSession.objects.create(user=self.other)
        QuestionAttempt.objects.create(
            user=self.other,
            question=self.questions_a[0],
            test=self.test_a,
            session=other_session,
            is_correct=False,
            sr_next_review=None,
        )
        stats = self.client.get(self.STATS_URL).data
        self.assertEqual(stats['struggling_count'], 0)
        self.assertEqual(stats['due_count'], 0)

    def test_queue_fills_leftover_slots_with_struggling(self):
        """When there are no new cards, struggling should fill the requested limit."""
        extras = [self._make_question(self.test_a, f'extra {i}') for i in range(20)]
        for q in list(self.questions_a) + extras:
            self._attempt(q, is_correct=False, rating=None, next_review=None)

        response = self.client.get(self.QUEUE_URL, {'limit': 20})
        self.assertEqual(response.data['count'], 20)

    def test_stats_total_queued_matches_queue_at_cap(self):
        extras = [self._make_question(self.test_a, f'stats extra {i}') for i in range(20)]
        for q in list(self.questions_a) + extras:
            self._attempt(q, is_correct=False, rating=None, next_review=None)

        stats = self.client.get(self.STATS_URL).data
        queue = self.client.get(self.QUEUE_URL, {'limit': 50}).data
        self.assertEqual(stats['struggling_count'], 26)
        self.assertEqual(stats['total_queued'], queue['count'])
        self.assertEqual(queue['count'], 26)

    def test_test_ids_filter_restricts_queue(self):
        self._attempt(self.questions_a[0], is_correct=False, rating=None)
        self._attempt(self.questions_b[0], is_correct=False, rating=None)

        response = self.client.get(
            self.QUEUE_URL,
            {'limit': 20, 'test_ids': str(self.test_b.id)},
        )
        ids = {item['id'] for item in response.data['questions']}
        self.assertNotIn(str(self.questions_a[0].id), ids)
        self.assertIn(str(self.questions_b[0].id), ids)

    def test_mastered_count_uses_sr_thresholds(self):
        self._attempt(
            self.questions_a[0],
            rating='easy',
            next_review=date.today() + timedelta(days=30),
            reps=4,
            interval=21,
        )
        stats = self.client.get(self.STATS_URL).data
        self.assertEqual(stats['mastered_count'], 1)
        self.assertEqual(stats['due_count'], 0)
