from __future__ import annotations

import re
from typing import Any

CLOSED_TYPES = ("single-choice", "multiple-choice")
OPEN_TYPES = ("open-text", "open-cli", "open-code")
LEGACY_OPEN_TYPES = ("open", "open-ended")
ALL_TYPES = CLOSED_TYPES + OPEN_TYPES + LEGACY_OPEN_TYPES

CATASTROPHIC_REGEX = [
    r"\(.*\+.*\)\+",
    r"\(.*\*.*\)\*",
    r"\(.*\|.*\)\+",
    r"\(.*\|.*\)\*",
]


def validate_quiz(data: Any) -> list[dict]:
    issues: list[dict] = []

    def add(path: str, code: str, message: str) -> None:
        issues.append({"path": path, "code": code, "message": message})

    if not isinstance(data, dict):
        add("", "INVALID_TYPE", "Quiz document must be a JSON object.")
        return issues

    for field in ("scope", "category", "questions"):
        if field not in data:
            add(field, "MISSING_FIELD", f"Missing '{field}'.")

    if "questions" in data:
        if not isinstance(data["questions"], list):
            add("questions", "INVALID_TYPE", "'questions' must be a list.")
        elif len(data["questions"]) == 0:
            add("questions", "EMPTY_QUESTIONS", "'questions' must not be empty.")
        else:
            seen_ids: dict[int, int] = {}
            seen_text: dict[str, int] = {}
            for i, question in enumerate(data["questions"]):
                _validate_question(question, i, add)
                if isinstance(question, dict):
                    sid = question.get("id")
                    if isinstance(sid, int):
                        if sid in seen_ids:
                            add(
                                f"questions[{i}].id",
                                "DUPLICATE_SOURCE_ID",
                                f"Duplicate id {sid} (also questions[{seen_ids[sid]}]).",
                            )
                        else:
                            seen_ids[sid] = i
                    text = question.get("questionText")
                    if isinstance(text, str) and text in seen_text:
                        add(
                            f"questions[{i}].questionText",
                            "DUPLICATE_QUESTION_TEXT",
                            f"Duplicate questionText (also questions[{seen_text[text]}]).",
                        )
                    elif isinstance(text, str):
                        seen_text[text] = i

    if "version" in data and data["version"] is not None and not isinstance(data["version"], str):
        add("version", "INVALID_TYPE", "'version' must be a string.")
    if "description" in data and data["description"] is not None and not isinstance(data["description"], str):
        add("description", "INVALID_TYPE", "'description' must be a string.")

    return issues


def _validate_question(question: Any, index: int, add) -> None:
    prefix = f"questions[{index}]"
    if not isinstance(question, dict):
        add(prefix, "INVALID_TYPE", "Question must be a JSON object.")
        return

    for field in ("questionText", "type"):
        if field not in question:
            add(f"{prefix}.{field}", "MISSING_FIELD", f"Missing '{field}'.")

    q_type = question.get("type")
    if q_type is not None and q_type not in ALL_TYPES:
        add(f"{prefix}.type", "INVALID_QUESTION_TYPE", f"Invalid question type '{q_type}'.")
        return

    if q_type in CLOSED_TYPES:
        if "options" not in question or "correctAnswers" not in question:
            if "options" not in question:
                add(f"{prefix}.options", "MISSING_FIELD", "Missing 'options'.")
            if "correctAnswers" not in question:
                add(f"{prefix}.correctAnswers", "MISSING_FIELD", "Missing 'correctAnswers'.")
        else:
            options = question["options"]
            correct = question["correctAnswers"]
            if not isinstance(options, list) or len(options) < 2:
                add(f"{prefix}.options", "INVALID_TYPE", "'options' must be a list of at least 2 items.")
            if not isinstance(correct, list) or not correct:
                add(f"{prefix}.correctAnswers", "INVALID_CORRECT_ANSWERS", "'correctAnswers' must be a non-empty list.")
            else:
                if q_type == "single-choice" and len(correct) != 1:
                    add(
                        f"{prefix}.correctAnswers",
                        "INVALID_CORRECT_ANSWERS",
                        "single-choice requires exactly one correct answer.",
                    )
                if isinstance(options, list):
                    for idx in correct:
                        if not isinstance(idx, int) or not 0 <= idx < len(options):
                            add(
                                f"{prefix}.correctAnswers",
                                "INVALID_CORRECT_ANSWERS",
                                f"Invalid correctAnswers index: {idx}.",
                            )

    if q_type in OPEN_TYPES + LEGACY_OPEN_TYPES:
        if "gradingCriteria" not in question or "maxPoints" not in question:
            add(
                f"{prefix}",
                "MISSING_GRADING_CONFIG",
                "Open questions require 'gradingCriteria' and 'maxPoints'.",
            )
        else:
            criteria = question.get("gradingCriteria")
            max_points = question.get("maxPoints")
            if not isinstance(criteria, str) or not criteria.strip():
                add(f"{prefix}.gradingCriteria", "MISSING_GRADING_CONFIG", "'gradingCriteria' must be a non-empty string.")
            if not isinstance(max_points, int) or not 1 <= max_points <= 100:
                add(f"{prefix}.maxPoints", "MISSING_GRADING_CONFIG", "'maxPoints' must be an integer 1–100.")
            if q_type == "open-cli" and isinstance(criteria, str) and criteria:
                regex_error = _validate_regex(criteria)
                if regex_error:
                    add(f"{prefix}.gradingCriteria", "INVALID_REGEX", regex_error)
            if q_type == "open-code" and isinstance(criteria, str) and ":" not in criteria:
                add(
                    f"{prefix}.gradingCriteria",
                    "INVALID_CODE_CRITERIA",
                    "open-code gradingCriteria must start with a language prefix (e.g. 'python: ...').",
                )

    if "explanation" in question and question["explanation"] is not None and not isinstance(question["explanation"], str):
        add(f"{prefix}.explanation", "INVALID_TYPE", "'explanation' must be a string.")
    if "image" in question and question["image"] is not None and not isinstance(question["image"], str):
        add(f"{prefix}.image", "INVALID_TYPE", "'image' must be a string.")
    if "tags" in question and not isinstance(question["tags"], list):
        add(f"{prefix}.tags", "INVALID_TYPE", "'tags' must be a list.")


def _validate_regex(pattern: str) -> str | None:
    for cp in CATASTROPHIC_REGEX:
        if re.search(cp, pattern):
            return f"Pattern looks catastrophically backtracking: {pattern!r}"
    try:
        re.compile(pattern)
    except re.error as e:
        return f"Invalid regex: {e}"
    return None


def normalize_question_type(q_type: str) -> str:
    if q_type in LEGACY_OPEN_TYPES:
        return "open-text"
    return q_type
