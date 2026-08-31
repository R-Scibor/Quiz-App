from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from api_v1.models import Answer, Category, Question, QuestionAttempt, QuizSession, Tag, Test
from api_v1.quiz_export import question_to_interchange, test_to_interchange
from api_v1.quiz_import import ImportConflictError, ImportValidationError, import_quiz


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


def _sample(scope="Medieval Poland"):
    return {
        "category": "History",
        "scope": scope,
        "version": "1.0",
        "description": "from file",
        "questions": [
            {
                "id": 1,
                "questionText": "Coronation year?",
                "type": "single-choice",
                "options": ["966", "1025"],
                "correctAnswers": [1],
                "tags": ["dates"],
                "image": "",
                "explanation": "1025",
            },
            {
                "id": 2,
                "questionText": "Explain the baptism of Poland.",
                "type": "open-text",
                "gradingCriteria": "Must mention 966.",
                "maxPoints": 3,
                "tags": ["baptism"],
            },
        ],
    }


class ImportQuizTests(TestCase):
    def test_create_assigns_uuids_and_source_id(self):
        result = import_quiz(_sample())
        self.assertTrue(result["applied"])
        self.assertEqual(result["test"]["action"], "create")
        quiz = result["quiz"]
        self.assertEqual(len(quiz["questions"]), 2)
        self.assertEqual(quiz["questions"][0]["id"], 1)
        self.assertTrue(quiz["questions"][0]["question_id"])
        t = Test.objects.get(title="Medieval Poland")
        self.assertEqual(t.version, "1.0")
        self.assertEqual(t.questions.get(source_id=1).text, "Coronation year?")

    def test_second_import_same_source_id_preserves_question_uuid(self):
        first = import_quiz(_sample())
        qid = first["quiz"]["questions"][0]["question_id"]
        payload = _sample()
        payload["questions"][0]["explanation"] = "Updated"
        second = import_quiz(payload)
        self.assertEqual(second["quiz"]["questions"][0]["question_id"], qid)
        self.assertEqual(Question.objects.get(id=qid).explanation, "Updated")
        self.assertEqual(Question.objects.filter(test_id=first["test"]["test_id"]).count(), 2)

    def test_match_by_text_when_id_missing_then_backfill_source_id(self):
        import_quiz(_sample())
        payload = _sample()
        payload["questions"][0]["id"] = 99  # same text, new source_id → match by text
        result = import_quiz(payload)
        q = Question.objects.get(text="Coronation year?")
        self.assertEqual(q.source_id, 99)
        self.assertIn("source_id", result["questions"]["updated"][0]["fields"])

    def test_does_not_delete_question_with_attempts(self):
        first = import_quiz(_sample())
        t = Test.objects.get(id=first["test"]["test_id"])
        q = t.questions.get(source_id=2)
        user = User.objects.create_user("u", password="p")
        session = QuizSession.objects.create(user=user)
        QuestionAttempt.objects.create(
            user=user, question=q, test=t, session=session, is_correct=True
        )
        payload = _sample()
        payload["questions"] = [payload["questions"][0]]
        result = import_quiz(payload)
        self.assertTrue(Question.objects.filter(id=q.id).exists())
        self.assertEqual(len(result["questions"]["blocked_deletes"]), 1)
        self.assertEqual(result["questions"]["blocked_deletes"][0]["reason"], "has_attempts")

    def test_deletes_question_without_attempts_when_omitted(self):
        first = import_quiz(_sample())
        t = Test.objects.get(id=first["test"]["test_id"])
        q = t.questions.get(source_id=2)
        payload = _sample()
        payload["questions"] = [payload["questions"][0]]
        import_quiz(payload)
        self.assertFalse(Question.objects.filter(id=q.id).exists())

    def test_dry_run_writes_nothing(self):
        result = import_quiz(_sample(), dry_run=True)
        self.assertFalse(result["applied"])
        self.assertTrue(result["dry_run"])
        self.assertEqual(Test.objects.count(), 0)
        self.assertIsNone(result["quiz"])

    def test_invalid_json_raises_before_write(self):
        with self.assertRaises(ImportValidationError):
            import_quiz({"category": "X", "scope": "Y", "questions": []})
        self.assertEqual(Test.objects.count(), 0)

    def test_unknown_test_id_raises(self):
        import uuid
        from api_v1.quiz_import import TestNotFoundError
        with self.assertRaises(TestNotFoundError):
            import_quiz(_sample(), test_id=uuid.uuid4())

    def test_match_does_not_reuse_already_bound_row(self):
        def _closed(qid, text):
            return {
                "id": qid,
                "questionText": text,
                "type": "single-choice",
                "options": ["3", "4"],
                "correctAnswers": [1],
            }

        initial = {
            "category": "Math",
            "scope": "Arithmetic",
            "version": "1.0",
            "questions": [_closed(1, "What is 2+2?")],
        }
        first = import_quiz(initial)
        original_id = Question.objects.get(source_id=1, test_id=first["test"]["test_id"]).id
        payload = {
            "category": "Math",
            "scope": "Arithmetic",
            "version": "1.0",
            "questions": [
                _closed(1, "What is 2+2? (integer)"),
                _closed(2, "What is 2+2?"),
            ],
        }
        import_quiz(payload)
        q1 = Question.objects.get(source_id=1)
        q2 = Question.objects.get(source_id=2)
        self.assertNotEqual(q1.id, q2.id)
        self.assertEqual(q1.id, original_id)
        self.assertEqual(q1.text, "What is 2+2? (integer)")
        self.assertEqual(q2.text, "What is 2+2?")
        self.assertEqual(Question.objects.filter(test_id=first["test"]["test_id"]).count(), 2)

    def test_identical_reimport_is_unchanged(self):
        import_quiz(_sample())
        second = import_quiz(_sample())
        self.assertEqual(second["questions"]["unchanged"], 2)
        for item in second["questions"]["updated"]:
            self.assertNotIn("options", item["fields"])
            self.assertNotIn("correctAnswers", item["fields"])

    def test_ambiguous_title_raises(self):
        Test.objects.create(title="Medieval Poland")
        Test.objects.create(title="Medieval Poland")
        with self.assertRaises(ImportConflictError):
            import_quiz(_sample())
