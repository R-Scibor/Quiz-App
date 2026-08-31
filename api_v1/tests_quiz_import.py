from django.db import IntegrityError
from django.test import TestCase

from api_v1.models import Test, Question


class SourceIdConstraintTests(TestCase):
    def test_source_id_unique_per_test(self):
        t = Test.objects.create(title="T")
        Question.objects.create(test=t, text="Q1", source_id=1)
        with self.assertRaises(IntegrityError):
            Question.objects.create(test=t, text="Q2", source_id=1)

    def test_null_source_ids_allowed_twice(self):
        t = Test.objects.create(title="T")
        Question.objects.create(test=t, text="Q1", source_id=None)
        Question.objects.create(test=t, text="Q2", source_id=None)
        self.assertEqual(t.questions.count(), 2)
