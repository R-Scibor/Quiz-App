import os
import re
import json
import time
import logging
import unicodedata
from html.parser import HTMLParser

import requests
from celery import shared_task
import google.generativeai as genai
from .models import PromptConfiguration

logger = logging.getLogger(__name__)

VECTOR_SERVICE_URL = os.environ.get("VECTOR_SERVICE_URL", "http://ai_grader:8001")
VECTOR_TIMEOUT = 3  # seconds per attempt
VECTOR_PASS_THRESHOLD = 0.85
VECTOR_FAIL_THRESHOLD = 0.30


# ---------------------------------------------------------------------------
# Text sanitizers
# ---------------------------------------------------------------------------

class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def get_text(self):
        return " ".join(self._parts)


def sanitize_text(text: str) -> str:
    """Strip HTML tags, collapse whitespace, normalize unicode."""
    stripper = _HTMLStripper()
    stripper.feed(text)
    plain = stripper.get_text()
    plain = unicodedata.normalize("NFKC", plain)
    return " ".join(plain.split())


def sanitize_cli(text: str) -> str:
    """Strip leading/trailing whitespace, collapse internal runs of spaces to one."""
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Vector microservice client
# ---------------------------------------------------------------------------

def call_vector_service(student: str, reference: str) -> float | None:
    """
    POST to the vector similarity microservice.
    Returns the similarity score (0–1) or None on failure.
    Retries once on connection error.
    """
    url = f"{VECTOR_SERVICE_URL}/compare"
    payload = {"student_answer": student, "reference_answer": reference}
    for attempt in range(2):
        try:
            resp = requests.post(url, json=payload, timeout=VECTOR_TIMEOUT)
            resp.raise_for_status()
            return float(resp.json()["similarity_score"])
        except Exception as exc:
            if attempt == 0:
                logger.warning("Vector service call failed (attempt 1): %s. Retrying.", exc)
            else:
                logger.warning("Vector service call failed (attempt 2): %s. Falling back to LLM.", exc)
    return None


# ---------------------------------------------------------------------------
# Gemini LLM helper
# ---------------------------------------------------------------------------

def _call_gemini(question_text: str, grading_criteria: str, max_points: int,
                 user_answer: str, system_prompt_override: str | None = None) -> dict:
    """
    Call Gemini 2.5 Flash and return a dict with at minimum 'score' and 'feedback'.
    Raises on error.
    """
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured on the server.")

    if system_prompt_override:
        prompt = system_prompt_override.format(
            question_text=question_text,
            grading_criteria=grading_criteria,
            max_points=max_points,
            user_answer=user_answer,
        )
    else:
        prompt_config = PromptConfiguration.objects.filter(is_active=True).first()
        if not prompt_config:
            raise RuntimeError("No active PromptConfiguration found in the database.")
        prompt = prompt_config.prompt_text.format(
            question_text=question_text,
            grading_criteria=grading_criteria,
            max_points=max_points,
            user_answer=user_answer,
        )

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    ai_response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            thinking_config={"thinking_budget": 0},
        ),
    )

    cleaned = ai_response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned invalid JSON: %s. Raw (500 chars): %s", exc, cleaned[:500])
        raise ValueError(f"Gemini returned invalid JSON: {exc}") from exc

    if "score" not in result or "feedback" not in result:
        raise ValueError("Gemini response missing 'score' or 'feedback' keys.")

    return result


# ---------------------------------------------------------------------------
# Per-type grading pipelines
# ---------------------------------------------------------------------------

def grade_open_text(question_text: str, grading_criteria: str, max_points: int,
                    user_answer: str, force_llm: bool = False) -> dict:
    """Vector → threshold routing → Gemini fallback."""
    start = time.monotonic()
    student = sanitize_text(user_answer)
    reference = sanitize_text(grading_criteria) if grading_criteria else ""

    vector_score = None
    grading_method = "llm"

    if not force_llm and reference:
        vector_score = call_vector_service(student, reference)

    if vector_score is not None:
        if vector_score >= VECTOR_PASS_THRESHOLD:
            grading_method = "vector_pass"
            return {
                "score": max_points,
                "max_points": max_points,
                "feedback": "Correct — strong semantic match.",
                "grading_method": grading_method,
                "vector_score": vector_score,
                "latency_ms": int((time.monotonic() - start) * 1000),
            }
        elif vector_score < VECTOR_FAIL_THRESHOLD:
            grading_method = "vector_fail"
            return {
                "score": 0,
                "max_points": max_points,
                "feedback": "Incorrect — answer does not match expected meaning.",
                "grading_method": grading_method,
                "vector_score": vector_score,
                "latency_ms": int((time.monotonic() - start) * 1000),
            }
        else:
            grading_method = "llm"
    else:
        grading_method = "fallback_llm"

    result = _call_gemini(question_text, grading_criteria, max_points, user_answer)
    result.setdefault("max_points", max_points)
    result["grading_method"] = grading_method
    result["vector_score"] = vector_score
    result["latency_ms"] = int((time.monotonic() - start) * 1000)
    return result


def grade_open_cli(question_text: str, grading_criteria: str, max_points: int,
                   user_answer: str, force_llm: bool = False) -> dict:
    """Exact match → regex match (gradingCriteria) → Gemini fallback."""
    start = time.monotonic()
    normalized = sanitize_cli(user_answer)

    # Regex match against gradingCriteria
    if not force_llm and grading_criteria:
        try:
            if re.fullmatch(grading_criteria, normalized, re.IGNORECASE):
                return {
                    "score": max_points,
                    "max_points": max_points,
                    "feedback": "Correct — command matches the expected pattern.",
                    "grading_method": "regex_pass",
                    "vector_score": None,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                }
        except re.error as exc:
            logger.warning("Regex match error for CLI question: %s", exc)

    # Gemini fallback with CLI-specific system prompt
    cli_system_prompt = (
        "You are a strict CLI command grader. "
        "Accept only valid, safe commands that fulfil the requirement. "
        "Reject commands with destructive flags (--force, -f with rm, --delete, etc.). "
        "Award 0 points for any unsafe or incorrect command.\n\n"
        "Question: {question_text}\n"
        "Expected pattern / criteria: {grading_criteria}\n"
        "Max points: {max_points}\n"
        "Student answer: {user_answer}\n\n"
        'Respond ONLY with JSON: {{"score": <int>, "feedback": "<string>"}}'
    )
    result = _call_gemini(question_text, grading_criteria, max_points, user_answer,
                          system_prompt_override=cli_system_prompt)
    result.setdefault("max_points", max_points)
    result["grading_method"] = "llm"
    result["vector_score"] = None
    result["latency_ms"] = int((time.monotonic() - start) * 1000)
    return result


def grade_open_code(question_text: str, grading_criteria: str, max_points: int,
                    user_answer: str) -> dict:
    """Always Gemini with a code-specific rubric prompt."""
    start = time.monotonic()

    # Parse language from "python: ..." prefix
    language = "unknown"
    if grading_criteria and ":" in grading_criteria:
        language = grading_criteria.split(":", 1)[0].strip()

    code_system_prompt = (
        "You are a code reviewer. Evaluate correctness, not style. "
        "Award partial credit for partially correct logic. "
        f"Language: {language}\n"
        "Requirements: {grading_criteria}\n\n"
        "Question: {question_text}\n"
        "Max points: {max_points}\n"
        "Student answer:\n{user_answer}\n\n"
        'Respond ONLY with JSON: {{"score": <int>, "feedback": "<string>"}}'
    )
    result = _call_gemini(question_text, grading_criteria, max_points, user_answer,
                          system_prompt_override=code_system_prompt)
    result.setdefault("max_points", max_points)
    result["grading_method"] = "llm"
    result["vector_score"] = None
    result["latency_ms"] = int((time.monotonic() - start) * 1000)
    return result


# ---------------------------------------------------------------------------
# Main Celery task
# ---------------------------------------------------------------------------

@shared_task
def generate_ai_answer(user_answer, grading_criteria, question_text, max_points,
                       question_type="open-text", force_llm=False):
    """
    Route grading based on question_type:
      open-text  → vector similarity → Gemini fallback
      open-cli   → regex → Gemini fallback
      open-code  → Gemini only (code rubric)
      open-ended → treated as open-text (legacy)

    force_llm=True skips local methods (vector/regex) and goes straight to Gemini.
    """
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        logger.critical("GEMINI_API_KEY is not configured on the server.")
        return {"error": "API_KEY_MISSING", "message": "AI API key is not configured on the server."}

    try:
        if question_type in ("open-text", "open-ended"):
            return grade_open_text(question_text, grading_criteria, max_points, user_answer, force_llm=force_llm)
        elif question_type == "open-cli":
            return grade_open_cli(question_text, grading_criteria, max_points, user_answer, force_llm=force_llm)
        elif question_type == "open-code":
            return grade_open_code(question_text, grading_criteria, max_points, user_answer)
        else:
            # Unknown type — fall back to open-text pipeline
            logger.warning("Unknown question_type '%s', defaulting to open-text pipeline.", question_type)
            return grade_open_text(question_text, grading_criteria, max_points, user_answer, force_llm=force_llm)
    except Exception as exc:
        logger.exception("Unexpected error during grading: %s", exc)
        raise
