"""
Unit tests for the SM-2 spaced repetition algorithm implemented in api_v1.views.compute_next_sr.

No database required — compute_next_sr is pure Python.
"""
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from api_v1.views import compute_next_sr


class ComputeNextSRTestCase(unittest.TestCase):
    """Pure unit tests for compute_next_sr(rating, is_correct, prev_ease, prev_interval, prev_reps)."""

    # -------------------------------------------------------------------------
    # First repetition (prev_reps=0)
    # -------------------------------------------------------------------------

    def test_first_rep_easy_correct_interval_is_one(self):
        """First attempt with easy rating always produces interval=1."""
        interval, ease, next_date, reps = compute_next_sr('easy', True, 2.5, 1, 0)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 1)

    def test_first_rep_easy_correct_ease_increases(self):
        """Easy rating (q=5) increases ease factor: new_ease = 2.5 + 0.1 - 0 = 2.6."""
        _, ease, _, _ = compute_next_sr('easy', True, 2.5, 1, 0)
        self.assertAlmostEqual(ease, 2.6, places=5)

    def test_first_rep_normal_correct_ease_slightly_decreases(self):
        """Normal rating (q=3): new_ease = 2.5 + 0.1 - 2*(0.08+0.04) = 2.5 - 0.14 = 2.36.
        NOTE: 'normal' actually decreases ease by 0.14 per rep — this may not match
        the intuition that 'normal' should be neutral. Document this behavior."""
        _, ease, _, _ = compute_next_sr('normal', True, 2.5, 1, 0)
        self.assertAlmostEqual(ease, 2.36, places=5)

    def test_first_rep_hard_correct_resets_reps(self):
        """Hard rating (q=1) causes q<3 → reps reset to 0, interval=1."""
        interval, _, _, reps = compute_next_sr('hard', True, 2.5, 1, 0)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 0)

    def test_first_rep_incorrect_resets_reps(self):
        """Incorrect answer caps q at min(original_q, 1) → same as hard, reps=0."""
        interval, _, _, reps = compute_next_sr('easy', False, 2.5, 1, 0)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 0)

    # -------------------------------------------------------------------------
    # Second repetition (prev_reps=1)
    # -------------------------------------------------------------------------

    def test_second_rep_easy_correct_interval_is_six(self):
        """Second attempt (prev_reps=1) with easy rating produces interval=6."""
        interval, _, _, reps = compute_next_sr('easy', True, 2.5, 1, 1)
        self.assertEqual(interval, 6)
        self.assertEqual(reps, 2)

    def test_second_rep_normal_correct_interval_is_six(self):
        """Second attempt with normal rating also produces interval=6."""
        interval, _, _, reps = compute_next_sr('normal', True, 2.5, 1, 1)
        self.assertEqual(interval, 6)
        self.assertEqual(reps, 2)

    # -------------------------------------------------------------------------
    # Third and subsequent repetitions (prev_reps >= 2)
    # -------------------------------------------------------------------------

    def test_third_rep_easy_interval_uses_ease_factor(self):
        """Third attempt (prev_reps=2): interval = round(prev_interval * prev_ease)."""
        prev_interval = 6
        prev_ease = 2.5
        expected_interval = round(prev_interval * prev_ease)  # 15
        interval, _, _, reps = compute_next_sr('easy', True, prev_ease, prev_interval, 2)
        self.assertEqual(interval, expected_interval)
        self.assertEqual(reps, 3)

    def test_third_rep_hard_correct_resets(self):
        """Hard+correct at any rep level: q=1 < 3 → reps=0, interval=1."""
        interval, _, _, reps = compute_next_sr('hard', True, 2.5, 15, 5)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 0)

    def test_incorrect_at_high_reps_resets(self):
        """Incorrect answer at high rep count still resets."""
        interval, _, _, reps = compute_next_sr('easy', False, 2.5, 30, 10)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 0)

    # -------------------------------------------------------------------------
    # Ease factor bounds
    # -------------------------------------------------------------------------

    def test_ease_floor_never_goes_below_1_3(self):
        """Repeated hard answers drive ease toward minimum but never below 1.3."""
        ease = 2.5
        for _ in range(20):
            _, ease, _, _ = compute_next_sr('hard', True, ease, 1, 0)
        self.assertGreaterEqual(ease, 1.3)

    def test_easy_rating_increases_ease(self):
        """Easy rating (q=5): delta = 0.1 - 0*(0.08+0) = +0.1."""
        _, new_ease, _, _ = compute_next_sr('easy', True, 2.0, 1, 0)
        self.assertGreater(new_ease, 2.0)

    # -------------------------------------------------------------------------
    # next_review_date
    # -------------------------------------------------------------------------

    def test_next_review_date_is_today_plus_interval(self):
        """next_review_date must equal date.today() + timedelta(days=interval)."""
        with patch('api_v1.views.date') as mock_date:
            frozen_today = date(2025, 6, 1)
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            interval, _, next_date, _ = compute_next_sr('easy', True, 2.5, 1, 1)
            self.assertEqual(next_date, frozen_today + timedelta(days=interval))

    # -------------------------------------------------------------------------
    # Unknown / default rating
    # -------------------------------------------------------------------------

    def test_unknown_rating_defaults_to_q3_normal(self):
        """An unrecognised rating string defaults to q=3 (same as 'normal')."""
        interval_normal, ease_normal, _, reps_normal = compute_next_sr('normal', True, 2.5, 1, 1)
        interval_unk, ease_unk, _, reps_unk = compute_next_sr('bogus_rating', True, 2.5, 1, 1)
        self.assertEqual(interval_normal, interval_unk)
        self.assertAlmostEqual(ease_normal, ease_unk, places=5)
        self.assertEqual(reps_normal, reps_unk)
