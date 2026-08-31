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

    def test_export_questions_follow_source_id_not_uuid(self):
        t = Test.objects.create(title="T")
        q2 = Question.objects.create(test=t, text="Second", source_id=2)
        q1 = Question.objects.create(test=t, text="First", source_id=1)
        doc = test_to_interchange(t)
        self.assertEqual([qd["id"] for qd in doc["questions"]], [1, 2])
        self.assertEqual(
            [qd["question_id"] for qd in doc["questions"]],
            [str(q1.id), str(q2.id)],
        )

    def test_export_uses_prefetch_not_n_plus_one(self):
        t = Test.objects.create(title="T")
        q1 = Question.objects.create(
            test=t, text="Q1", question_type=Question.SINGLE_CHOICE, source_id=1
        )
        q2 = Question.objects.create(
            test=t, text="Q2", question_type=Question.SINGLE_CHOICE, source_id=2
        )
        Answer.objects.create(question=q1, text="a", is_correct=True)
        Answer.objects.create(question=q1, text="b", is_correct=False)
        Answer.objects.create(question=q2, text="c", is_correct=True)
        Answer.objects.create(question=q2, text="d", is_correct=False)
        tag = Tag.objects.create(name="t")
        q1.tags.add(tag)
        q2.tags.add(tag)

        # categories + questions + answers prefetch + tags prefetch
        with self.assertNumQueries(4):
            test_to_interchange(t)
