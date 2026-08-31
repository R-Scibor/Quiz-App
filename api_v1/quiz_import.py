from __future__ import annotations

import uuid

from django.db import IntegrityError, transaction
from django.db.models import Count

from api_v1.models import Answer, Category, Question, Tag, Test
from api_v1.quiz_export import test_to_interchange
from api_v1.quiz_validation import normalize_question_type, validate_quiz

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


def import_quiz(data: dict, *, test_id=None, dry_run: bool = False) -> dict:
    issues = validate_quiz(data)
    if issues:
        raise ImportValidationError(issues)

    if test_id is not None:
        try:
            test = Test.objects.get(pk=test_id)
        except Test.DoesNotExist as exc:
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

    warnings = [
        f"Question {b['question_id']} not deleted: has_attempts"
        for b in blocked
    ]

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
            unmatched.filter(attempts__isnull=True).delete()

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
