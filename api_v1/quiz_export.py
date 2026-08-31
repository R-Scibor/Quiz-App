from django.db.models import Prefetch

from api_v1.models import Answer, Question, Test

CLOSED = {Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE}


def question_to_interchange(question: Question) -> dict:
    # UUID PKs make Meta.ordering=['id'] non-insertion; drop it so options
    # follow creation order (SQLite rowid; importer insert order on Postgres).
    answers = list(question.answers.order_by())
    payload = {
        "id": question.source_id,
        "question_id": str(question.id),
        "questionText": question.text,
        "image": question.image or "",
        "type": question.question_type,
        "tags": [t.name for t in question.tags.all()],
        "explanation": question.explanation or "",
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
    questions = test.questions.prefetch_related(
        Prefetch("answers", queryset=Answer.objects.order_by()),
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
