from django.db.models import Prefetch

from api_v1.models import Answer, Question, Test

CLOSED = {Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE}


def question_to_interchange(question: Question) -> dict:
    # Prefetch(to_attr=...) for bulk export; otherwise drop UUID Meta.ordering.
    answers = getattr(question, "prefetched_answers", None)
    if answers is None:
        answers = list(question.answers.order_by())
    payload = {
        "id": question.source_id,
        "question_id": str(question.id),
        "questionText": question.text,
        "image": question.image or "",
        "type": question.question_type,
        "tags": [t.name for t in question.tags.all()],
        "explanation": question.explanation or "",
        "retired": bool(question.retired),
    }
    if question.question_type in CLOSED:
        payload["options"] = [a.text for a in answers]
        payload["correctAnswers"] = [i for i, a in enumerate(answers) if a.is_correct]
    else:
        payload["gradingCriteria"] = question.grading_criteria
        payload["maxPoints"] = question.max_points
    return payload


def test_to_interchange(test: Test) -> dict:
    cat = test.categories.order_by("name").first()
    questions = test.questions.order_by("source_id").prefetch_related(
        Prefetch(
            "answers",
            queryset=Answer.objects.order_by(),
            to_attr="prefetched_answers",
        ),
        "tags",
    ).all()
    return {
        "test_id": str(test.id),
        "category": cat.name if cat else "",
        "scope": test.title,
        "version": test.version,
        "description": test.description or "",
        "questions": [question_to_interchange(q) for q in questions],
    }
