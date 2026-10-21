from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Max

from api_v1.models import Answer, Category, Question, QuestionAttempt, Tag, Test
from api_v1.quiz_export import question_to_interchange, test_to_interchange
from api_v1.quiz_validation import normalize_question_type, validate_question, validate_quiz

CLOSED = {Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE}


class ImportValidationError(Exception):
    def __init__(self, issues: list[dict]):
        self.issues = issues
        super().__init__("VALIDATION_FAILED")


class TestNotFoundError(Exception):
    pass


class ImportConflictError(Exception):
    def __init__(self, message: str = "IMPORT_CONFLICT"):
        super().__init__(message)


class DeleteBlockedError(Exception):
    def __init__(self, attempt_count: int):
        self.attempt_count = attempt_count
        super().__init__("DELETE_BLOCKED")


_QUESTION_FIELDS = {
    "id",
    "questionText",
    "image",
    "type",
    "tags",
    "options",
    "correctAnswers",
    "explanation",
    "gradingCriteria",
    "maxPoints",
    "retired",
}


def _next_source_id(test: Test) -> int:
    current = test.questions.aggregate(m=Max("source_id"))["m"]
    return (current or 0) + 1


def _duplicate_issues(test: Test, qdata: dict, *, exclude: Question | None = None) -> list[dict]:
    issues = []
    qs = test.questions.all()
    if exclude is not None:
        qs = qs.exclude(pk=exclude.pk)
    sid = qdata.get("id")
    if isinstance(sid, int) and qs.filter(source_id=sid).exists():
        issues.append({
            "path": "id",
            "code": "DUPLICATE_SOURCE_ID",
            "message": f"id {sid} is already used on this test.",
        })
    text = qdata.get("questionText")
    if isinstance(text, str) and qs.filter(text=text).exists():
        issues.append({
            "path": "questionText",
            "code": "DUPLICATE_QUESTION_TEXT",
            "message": "questionText is already used on this test.",
        })
    return issues


def _preview_question(qdata: dict) -> dict:
    ntype = normalize_question_type(qdata["type"])
    payload = {
        "id": qdata.get("id"),
        "question_id": qdata.get("question_id"),
        "questionText": qdata["questionText"],
        "image": qdata.get("image") or "",
        "type": ntype,
        "tags": [name for name in (qdata.get("tags") or []) if isinstance(name, str)],
        "explanation": qdata.get("explanation") or "",
        "retired": qdata["retired"] if isinstance(qdata.get("retired"), bool) else False,
    }
    if ntype in CLOSED:
        payload["options"] = list(qdata.get("options") or [])
        payload["correctAnswers"] = list(qdata.get("correctAnswers") or [])
    else:
        payload["gradingCriteria"] = qdata.get("gradingCriteria")
        payload["maxPoints"] = qdata.get("maxPoints")
    return payload


def create_question(test: Test, qdata: dict, *, dry_run: bool = False) -> dict:
    data = {k: v for k, v in qdata.items() if k in _QUESTION_FIELDS}
    if data.get("id") is None:
        data["id"] = _next_source_id(test)
    issues = validate_question(data)
    issues.extend(_duplicate_issues(test, data))
    if issues:
        raise ImportValidationError(issues)
    if dry_run:
        return {"applied": False, "dry_run": True, "question": _preview_question(data)}
    with transaction.atomic():
        obj = _upsert_question(test, None, data)
    return {"applied": True, "dry_run": False, "question": question_to_interchange(obj)}


def create_questions(test: Test, questions: Any, *, dry_run: bool = False) -> dict:
    if not isinstance(questions, list) or len(questions) == 0:
        raise ImportValidationError([{
            "path": "questions",
            "code": "EMPTY_QUESTIONS",
            "message": "'questions' must be a non-empty list.",
        }])
    if len(questions) > 50:
        raise ImportValidationError([{
            "path": "questions",
            "code": "INVALID_TYPE",
            "message": "A batch can contain at most 50 questions.",
        }])

    next_id = _next_source_id(test)
    seen_ids = set(test.questions.exclude(source_id=None).values_list("source_id", flat=True))
    seen_text = set(test.questions.values_list("text", flat=True))
    prepared = []
    issues: list[dict] = []
    for index, raw in enumerate(questions):
        data = {k: v for k, v in raw.items() if k in _QUESTION_FIELDS} if isinstance(raw, dict) else raw
        if isinstance(data, dict) and data.get("id") is None:
            data = dict(data)
            data["id"] = next_id
            next_id += 1
        for issue in validate_question(data):
            path = issue["path"]
            issue["path"] = f"questions[{index}].{path}" if path else f"questions[{index}]"
            issues.append(issue)
        if isinstance(data, dict):
            sid = data.get("id")
            if isinstance(sid, int):
                if sid in seen_ids:
                    issues.append({
                        "path": f"questions[{index}].id",
                        "code": "DUPLICATE_SOURCE_ID",
                        "message": f"id {sid} is already used.",
                    })
                else:
                    seen_ids.add(sid)
            text = data.get("questionText")
            if isinstance(text, str) and text.strip():
                if text in seen_text:
                    issues.append({
                        "path": f"questions[{index}].questionText",
                        "code": "DUPLICATE_QUESTION_TEXT",
                        "message": "questionText is already used on this test.",
                    })
                else:
                    seen_text.add(text)
        prepared.append(data)
    if issues:
        raise ImportValidationError(issues)
    if dry_run:
        return {
            "applied": False,
            "dry_run": True,
            "questions": [_preview_question(item) for item in prepared],
        }
    created = []
    with transaction.atomic():
        for item in prepared:
            created.append(question_to_interchange(_upsert_question(test, None, item)))
    return {"applied": True, "dry_run": False, "questions": created}


def update_question(question: Question, patch: dict, *, dry_run: bool = False) -> dict:
    merged = question_to_interchange(question)
    for key, value in patch.items():
        if key in _QUESTION_FIELDS:
            merged[key] = value
    issues = validate_question(merged)
    issues.extend(_duplicate_issues(question.test, merged, exclude=question))
    if issues:
        raise ImportValidationError(issues)
    if dry_run:
        return {"applied": False, "dry_run": True, "question": _preview_question(merged)}
    with transaction.atomic():
        obj = _upsert_question(question.test, question, merged)
    return {"applied": True, "dry_run": False, "question": question_to_interchange(obj)}


def delete_question(question: Question, *, dry_run: bool = False) -> dict:
    attempt_count = QuestionAttempt.objects.filter(question=question).count()
    if attempt_count:
        if dry_run:
            return {
                "applied": False,
                "dry_run": True,
                "deleted": False,
                "blocked": {"reason": "has_attempts", "attempt_count": attempt_count},
            }
        raise DeleteBlockedError(attempt_count)
    if dry_run:
        return {
            "applied": False,
            "dry_run": True,
            "deleted": False,
            "question_id": str(question.id),
        }
    question_id = str(question.id)
    question.delete()
    return {"applied": True, "dry_run": False, "deleted": True, "question_id": question_id}


def import_quiz(data: dict, *, test_id=None, dry_run: bool = False) -> dict:
    issues = validate_quiz(data)
    if issues:
        raise ImportValidationError(issues)

    if test_id is not None:
        try:
            test = Test.objects.get(pk=test_id)
        except (Test.DoesNotExist, ValidationError) as exc:
            raise TestNotFoundError(str(test_id)) from exc
    else:
        matches = list(Test.objects.filter(title=data["scope"]))
        if len(matches) > 1:
            raise ImportConflictError("IMPORT_CONFLICT")
        test = matches[0] if matches else None

    action = "update" if test is not None else "create"
    metadata_changes = {}
    if test is not None:
        if test.title != data["scope"]:
            metadata_changes["scope"] = {"from": test.title, "to": data["scope"]}
        new_version = data.get("version", test.version)
        if test.version != new_version:
            metadata_changes["version"] = {"from": test.version, "to": new_version}
        if "description" in data:
            new_desc = data.get("description") or ""
            old_desc = test.description or ""
            if old_desc != new_desc:
                metadata_changes["description"] = {"from": test.description, "to": new_desc}
    else:
        metadata_changes["scope"] = {"from": None, "to": data["scope"]}

    incoming = data["questions"]
    existing_by_id, existing_by_source, existing_by_text = _index_questions(test)

    created, updated, would_delete, blocked = [], [], [], []
    unchanged = 0
    matched_pks: set = set()
    planned: list[tuple] = []

    for qdata in incoming:
        match = _resolve(qdata, existing_by_id, existing_by_source, existing_by_text)
        if match is None:
            planned.append(("create", None, qdata, ["questionText"]))
        else:
            if match.pk in matched_pks:
                raise ImportConflictError("IMPORT_CONFLICT")
            matched_pks.add(match.pk)
            fields = _changed_fields(match, qdata)
            planned.append(("update" if fields else "unchanged", match, qdata, fields))

    if test is not None:
        for q in test.questions.annotate(attempt_count=Count("attempts")):
            if q.pk in matched_pks:
                continue
            entry = {
                "question_id": str(q.id),
                "source_id": q.source_id,
                "questionText": q.text,
            }
            if q.attempt_count:
                blocked.append({**entry, "reason": "has_attempts", "attempt_count": q.attempt_count})
            elif q.retired:
                blocked.append({**entry, "reason": "retired"})
            else:
                would_delete.append(entry)

    for kind, match, qdata, fields in planned:
        if kind == "create":
            created.append({"source_id": qdata.get("id"), "questionText": qdata["questionText"]})
        elif kind == "update":
            updated.append({
                "question_id": str(match.id),
                "source_id": qdata.get("id", match.source_id),
                "fields": fields,
            })
        else:
            unchanged += 1

    warnings = []
    for item in blocked:
        if item.get("reason") == "retired":
            warnings.append(f"Question {item['question_id']} not deleted: retired")
        else:
            warnings.append(f"Question {item['question_id']} not deleted: has_attempts")

    result = {
        "applied": False,
        "dry_run": dry_run,
        "test": {
            "test_id": str(test.id) if test is not None else None,
            "action": action,
            "metadata_changes": metadata_changes,
        },
        "questions": {
            "created": created,
            "updated": updated,
            "unchanged": unchanged,
            "would_delete": would_delete,
            "blocked_deletes": blocked,
        },
        "warnings": warnings,
        "errors": [],
        "quiz": None,
    }

    if dry_run:
        return result

    try:
        with transaction.atomic():
            if test is None:
                test = Test.objects.create(
                    title=data["scope"],
                    version=data.get("version") or "1.0",
                    description=data.get("description") or "",
                )
            else:
                test.title = data["scope"]
                test.version = data.get("version") or test.version
                if "description" in data:
                    test.description = data.get("description") or ""
                test.save()

            category_name = data.get("category") or ""
            if category_name:
                cat, _ = Category.objects.get_or_create(name=category_name)
                test.categories.set([cat])
            else:
                test.categories.clear()

            existing_by_id, existing_by_source, existing_by_text = _index_questions(test)
            keep: set = set()
            pairs: list[tuple] = []
            for qdata in incoming:
                match = _resolve(qdata, existing_by_id, existing_by_source, existing_by_text)
                if match is not None and match.pk in keep:
                    raise ImportConflictError("IMPORT_CONFLICT")
                pairs.append((match, qdata))
                if match is not None:
                    keep.add(match.pk)

            locked = test.questions.select_for_update()
            list(locked)
            unmatched = locked.exclude(pk__in=keep) if keep else locked
            unmatched.filter(attempts__isnull=True, retired=False).delete()

            _release_unique_slots(pairs)

            for match, qdata in pairs:
                _upsert_question(test, match, qdata)
    except IntegrityError as exc:
        raise ImportConflictError("IMPORT_CONFLICT") from exc

    test = Test.objects.prefetch_related(
        "questions__answers", "questions__tags", "categories"
    ).get(pk=test.pk)
    result["applied"] = True
    result["dry_run"] = False
    result["test"]["test_id"] = str(test.id)
    result["quiz"] = test_to_interchange(test)
    return result


def _qid_key(value) -> str | None:
    if value is None or value == "":
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return str(value)


def _index_questions(test: Test | None):
    existing_by_id = {}
    existing_by_source = {}
    existing_by_text = {}
    if test is None:
        return existing_by_id, existing_by_source, existing_by_text
    for q in test.questions.annotate(attempt_count=Count("attempts")):
        existing_by_id[str(q.id)] = q
        if q.source_id is not None:
            existing_by_source[q.source_id] = q
        existing_by_text[q.text] = q
    return existing_by_id, existing_by_source, existing_by_text


def _consume(question: Question, existing_by_id, existing_by_source, existing_by_text) -> None:
    existing_by_id.pop(str(question.id), None)
    if question.source_id is not None:
        bound = existing_by_source.get(question.source_id)
        if bound is not None and bound.pk == question.pk:
            existing_by_source.pop(question.source_id, None)
    bound_text = existing_by_text.get(question.text)
    if bound_text is not None and bound_text.pk == question.pk:
        existing_by_text.pop(question.text, None)


def _resolve(qdata, existing_by_id, existing_by_source, existing_by_text):
    match = None
    qid = _qid_key(qdata.get("question_id"))
    if qid and qid in existing_by_id:
        match = existing_by_id[qid]
    else:
        sid = qdata.get("id")
        if isinstance(sid, int) and sid in existing_by_source:
            match = existing_by_source[sid]
        else:
            text = qdata.get("questionText")
            if text in existing_by_text:
                match = existing_by_text[text]
    if match is not None:
        _consume(match, existing_by_id, existing_by_source, existing_by_text)
    return match


def _changed_fields(question: Question, qdata: dict) -> list[str]:
    fields = []
    if question.text != qdata["questionText"]:
        fields.append("questionText")
    ntype = normalize_question_type(qdata["type"])
    if question.question_type != ntype:
        fields.append("type")
    if qdata.get("id") is not None and question.source_id != qdata.get("id"):
        fields.append("source_id")
    if (question.explanation or "") != (qdata.get("explanation") or ""):
        fields.append("explanation")
    if (question.image or "") != (qdata.get("image") or ""):
        fields.append("image")
    if (question.grading_criteria or "") != (qdata.get("gradingCriteria") or ""):
        fields.append("gradingCriteria")
    if question.max_points != qdata.get("maxPoints"):
        fields.append("maxPoints")
    incoming_tags = [name for name in (qdata.get("tags") or []) if isinstance(name, str)]
    existing_tags = [t.name for t in question.tags.all()]
    if sorted(existing_tags) != sorted(incoming_tags):
        fields.append("tags")
    if ntype in CLOSED:
        answers = getattr(question, "prefetched_answers", None)
        if answers is None:
            answers = list(question.answers.order_by())
        if [a.text for a in answers] != list(qdata.get("options") or []):
            fields.append("options")
        existing_correct = [i for i, a in enumerate(answers) if a.is_correct]
        if existing_correct != list(qdata.get("correctAnswers") or []):
            fields.append("correctAnswers")
    if "retired" in qdata and isinstance(qdata["retired"], bool) and question.retired != qdata["retired"]:
        fields.append("retired")
    return fields


def _release_unique_slots(pairs: list[tuple]) -> None:
    """Clear unique (test, source_id) / (test, text) values before remapping."""
    for match, qdata in pairs:
        if match is None:
            continue
        updates = []
        new_text = qdata["questionText"]
        if match.text != new_text:
            match.text = f"__import_tmp__{match.pk}"
            updates.append("text")
        new_sid = qdata.get("id")
        if isinstance(new_sid, int) and match.source_id != new_sid:
            match.source_id = None
            updates.append("source_id")
        if updates:
            match.save(update_fields=updates)


def _upsert_question(test: Test, match: Question | None, qdata: dict) -> Question:
    ntype = normalize_question_type(qdata["type"])
    image = qdata.get("image") or None
    if image == "":
        image = None
    defaults = {
        "text": qdata["questionText"],
        "question_type": ntype,
        "explanation": qdata.get("explanation") or "",
        "grading_criteria": qdata.get("gradingCriteria"),
        "max_points": qdata.get("maxPoints"),
        "image": image,
        "source_id": qdata.get("id"),
        "test": test,
    }
    if "retired" in qdata and isinstance(qdata["retired"], bool):
        defaults["retired"] = qdata["retired"]
    elif match is None:
        defaults["retired"] = False
    if match is None:
        obj = Question.objects.create(**defaults)
    else:
        for key, value in defaults.items():
            setattr(match, key, value)
        match.save()
        obj = match

    tags = []
    for name in qdata.get("tags") or []:
        tag, _ = Tag.objects.get_or_create(name=name)
        tags.append(tag)
    obj.tags.set(tags)

    obj.answers.all().delete()
    if ntype in CLOSED:
        correct = set(qdata.get("correctAnswers") or [])
        for i, text in enumerate(qdata.get("options") or []):
            Answer.objects.create(question=obj, text=text, is_correct=i in correct)
    return obj
