from django.db import IntegrityError
from django.test import TestCase

from api_v1.models import Answer, Category, Tag, Test, Question
from api_v1.quiz_export import question_to_interchange, test_to_interchange


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


class ExportTests(TestCase):
    def test_export_closed_question_round_trip_shape(self):
        t = Test.objects.create(title="Medieval Poland", version="1.2", description="desc")
        cat = Category.objects.create(name="History")
        t.categories.add(cat)
        q = Question.objects.create(
            test=t,
            text="Coronation year?",
            question_type=Question.SINGLE_CHOICE,
            explanation="1025",
            source_id=1,
            image=None,
        )
        Answer.objects.create(question=q, text="966", is_correct=False)
        Answer.objects.create(question=q, text="1025", is_correct=True)
        tag = Tag.objects.create(name="dates")
        q.tags.add(tag)

        doc = test_to_interchange(t)
        self.assertEqual(doc["test_id"], str(t.id))
        self.assertEqual(doc["category"], "History")
        self.assertEqual(doc["scope"], "Medieval Poland")
        self.assertEqual(doc["version"], "1.2")
        self.assertEqual(doc["description"], "desc")
        qdoc = doc["questions"][0]
        self.assertEqual(qdoc["id"], 1)
        self.assertEqual(qdoc["question_id"], str(q.id))
        self.assertEqual(qdoc["questionText"], "Coronation year?")
        self.assertEqual(qdoc["type"], "single-choice")
        self.assertEqual(qdoc["options"], ["966", "1025"])
        self.assertEqual(qdoc["correctAnswers"], [1])
        self.assertEqual(qdoc["tags"], ["dates"])
        self.assertEqual(qdoc["image"], "")

    def test_export_open_question_uses_grading_fields(self):
        t = Test.objects.create(title="DNS")
        q = Question.objects.create(
            test=t,
            text="Explain DNS.",
            question_type=Question.OPEN_TEXT,
            grading_criteria="recursive lookup",
            max_points=3,
            source_id=2,
        )
        qdoc = question_to_interchange(q)
        self.assertEqual(qdoc["gradingCriteria"], "recursive lookup")
        self.assertEqual(qdoc["maxPoints"], 3)
        self.assertNotIn("options", qdoc)
