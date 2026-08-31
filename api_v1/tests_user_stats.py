"""
Tests for UserStatsView — streak calculation, accuracy, session counts.

The streak logic in api_v1/views.py:491-514 has a date-freezing caveat:
UserStatsView.get() has a LOCAL `from datetime import date, timedelta` at line 486
which re-binds `date` on every call, making module-level patches ineffective.

Therefore these tests create sessions relative to the ACTUAL date.today() so
that the real (unfrozen) date.today() inside the view still produces the expected
comparison results. Tests are therefore fully deterministic regardless of
when they run.
"""
import unittest
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status

from api_v1.models import QuizSession, Test, Question, QuestionAttempt

STATS_URL = '/api/v1/stats/'


class UserStatsStreakTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='stats_user', password='pass123')
        cls.token, _ = Token.objects.get_or_create(user=cls.user)

    def setUp(self):
        QuizSession.objects.filter(user=self.user).delete()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def _create_session(self, days_ago, completed=True, total=1, correct=1,
                        score=1.0, possible=1.0, study_mode=False):
        """
        Create a QuizSession with completed_at set to midnight UTC on
        (date.today() - days_ago). Uses real date.today() so the view's
        own date.today() comparison always matches.
        """
        target_date = date.today() - timedelta(days=days_ago)
        dt = timezone.make_aware(
            timezone.datetime.combine(target_date, timezone.datetime.min.time())
        )
        session = QuizSession.objects.create(
            user=self.user,
            is_study_mode=study_mode,
            total_questions=total,
            correct_count=correct,
            score_achieved=score,
            score_possible=possible,
        )
        if completed:
            session.completed_at = dt
            session.save()
        return session

    # -------------------------------------------------------------------------
    # No sessions
    # -------------------------------------------------------------------------

    def test_no_sessions_returns_zero_streaks_and_zero_accuracy(self):
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['current_streak_days'], 0)
        self.assertEqual(response.data['longest_streak_days'], 0)
        self.assertEqual(response.data['overall_accuracy'], 0)

    # -------------------------------------------------------------------------
    # Current streak
    # -------------------------------------------------------------------------

    def test_session_today_gives_current_streak_one(self):
        self._create_session(days_ago=0)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['current_streak_days'], 1)

    def test_session_yesterday_only_gives_current_streak_one(self):
        """
        A session only from yesterday (none today) returns current_streak=1.
        The code explicitly allows yesterday to 'not break yet' the streak
        (views.py:497-500). This test documents that intentional behavior.
        """
        self._create_session(days_ago=1)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['current_streak_days'], 1)

    def test_session_two_days_ago_only_gives_current_streak_zero(self):
        """A gap of 2+ days breaks the current streak entirely."""
        self._create_session(days_ago=2)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['current_streak_days'], 0)

    def test_consecutive_three_days_gives_current_streak_three(self):
        self._create_session(days_ago=0)
        self._create_session(days_ago=1)
        self._create_session(days_ago=2)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['current_streak_days'], 3)

    def test_gap_breaks_current_streak_counts_only_recent_run(self):
        """Sessions: today, yesterday, 3 days ago (gap at day 2). Current=2."""
        self._create_session(days_ago=0)
        self._create_session(days_ago=1)
        self._create_session(days_ago=3)  # gap at day 2
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['current_streak_days'], 2)

    # -------------------------------------------------------------------------
    # Longest streak
    # -------------------------------------------------------------------------

    def test_single_session_longest_streak_is_one(self):
        """
        A single completed date must give longest_streak=1.
        The loop initialises streak=1 before iterating, and
        longest_streak = max(longest_streak, streak) fires after the loop,
        so a single-date result produces max(0, 1)=1. This test guards
        against regressions to that logic.
        """
        self._create_session(days_ago=0)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['longest_streak_days'], 1)

    def test_longest_streak_picks_maximum_consecutive_run(self):
        """Sessions today+yesterday (run=2) and 10+11 days ago (run=2). Longest=2."""
        self._create_session(days_ago=0)
        self._create_session(days_ago=1)
        self._create_session(days_ago=10)
        self._create_session(days_ago=11)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['longest_streak_days'], 2)

    def test_longest_streak_five_consecutive(self):
        for d in range(5):
            self._create_session(days_ago=d)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['longest_streak_days'], 5)

    # -------------------------------------------------------------------------
    # Accuracy
    # -------------------------------------------------------------------------

    def test_accuracy_calculated_correctly(self):
        """3 correct out of 5 total → 60.0%."""
        self._create_session(days_ago=0, total=5, correct=3, score=3.0, possible=5.0)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['overall_accuracy'], 60.0)

    def test_perfect_accuracy(self):
        self._create_session(days_ago=0, total=4, correct=4, score=4.0, possible=4.0)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['overall_accuracy'], 100.0)

    # -------------------------------------------------------------------------
    # Incomplete sessions excluded
    # -------------------------------------------------------------------------

    def test_incomplete_session_excluded_from_all_stats(self):
        """Sessions without completed_at must not count toward any stat."""
        self._create_session(days_ago=0, completed=False)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['total_sessions'], 0)
        self.assertEqual(response.data['current_streak_days'], 0)

    # -------------------------------------------------------------------------
    # Session counts
    # -------------------------------------------------------------------------

    def test_total_sessions_includes_study_and_regular(self):
        """All completed sessions count toward total_sessions."""
        self._create_session(days_ago=0, study_mode=False)
        self._create_session(days_ago=1, study_mode=True)
        self._create_session(days_ago=2, study_mode=True)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.data['total_sessions'], 3)

    # -------------------------------------------------------------------------
    # Auth guard
    # -------------------------------------------------------------------------

    def test_stats_requires_auth(self):
        self.client.credentials()
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


STATS_TESTS_URL = '/api/v1/stats/tests/'


class StatsTestBreakdownTestCase(APITestCase):
    """Per-test accuracy must treat closed questions as 1 point when max_points is null."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='breakdown_user', password='pass123')
        cls.token, _ = Token.objects.get_or_create(user=cls.user)
        cls.test = Test.objects.create(title="Closed quiz")
        cls.closed_questions = [
            Question.objects.create(
                test=cls.test,
                text=f"Closed question {i}",
                question_type=Question.SINGLE_CHOICE,
                max_points=None,
            )
            for i in range(10)
        ]
        cls.open_question = Question.objects.create(
            test=cls.test,
            text="Open question",
            question_type=Question.OPEN_TEXT,
            grading_criteria="Mention X",
            max_points=6,
        )

    def setUp(self):
        QuestionAttempt.objects.filter(user=self.user).delete()
        QuizSession.objects.filter(user=self.user).delete()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.session = QuizSession.objects.create(user=self.user)

    def _attempt(self, question, points, is_correct):
        QuestionAttempt.objects.create(
            user=self.user,
            question=question,
            test=self.test,
            session=self.session,
            is_correct=is_correct,
            points_awarded=points,
        )

    def test_closed_only_attempts_count_null_max_points_as_one(self):
        """8/10 correct closed answers → 8/10 pts and 80% (not 8/0 and 0%)."""
        for i, q in enumerate(self.closed_questions):
            correct = i < 8
            self._attempt(q, points=1 if correct else 0, is_correct=correct)

        response = self.client.get(STATS_TESTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row['title'], "Closed quiz")
        self.assertEqual(row['total_attempts'], 10)
        self.assertEqual(row['points_earned'], 8)
        self.assertEqual(row['points_possible'], 10)
        self.assertEqual(row['accuracy'], 80.0)

    def test_mixed_closed_and_open_does_not_exceed_100_when_all_correct(self):
        """Closed 1pt + open 6pt, all correct → 7/7 100%, not 7/6 >100%."""
        self._attempt(self.closed_questions[0], points=1, is_correct=True)
        self._attempt(self.open_question, points=6, is_correct=True)

        response = self.client.get(STATS_TESTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = response.data[0]
        self.assertEqual(row['points_earned'], 7)
        self.assertEqual(row['points_possible'], 7)
        self.assertEqual(row['accuracy'], 100.0)
