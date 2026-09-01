# API Documentation

This document provides a detailed description of the API endpoints available in the Quiz App.

---

## Base URL

All API endpoints are prefixed with `/api/v1/`.

## Authentication

Most quiz endpoints (`/tests/`, `/questions/`, `/check_answer/`, `/task_result/`, `/report_issue/`) work without a token.

These endpoints require the header `Authorization: Token <token>`:

- `/auth/logout/`
- `/sessions/start/`
- `/sessions/<session_uuid>/complete/`
- `/attempts/`
- `/stats/`
- `/stats/tests/`
- `/study/queue/`
- `/study/stats/`

All `/authoring/*` endpoints require the same `Authorization: Token <token>` header **and** the authenticated user must have `is_staff=True`. Missing or invalid tokens receive `401 AUTHENTICATION_FAILED`. Non-staff tokens receive `403 PERMISSION_DENIED`.

Tokens are issued by `/auth/register/` and `/auth/login/`.

Question and answer primary keys are UUIDs, not integers. JSON import files still use a local integer `id` field; that value is stored as `source_id`, not as the database PK.

---

## Endpoints

### 1. List Available Tests

-   **Method:** `GET`
-   **Endpoint:** `/tests/`
-   **Description:** Retrieves a list of all available tests along with their metadata, including the number of open, closed, and total questions.
-   **Query Parameters:** None.
-   **Success Response (200 OK):**
    ```json
    [
        {
            "category": "History",
            "scope": "Medieval Poland",
            "version": "2.0-db",
            "test_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "question_counts": {
                "closed": 15,
                "open": 5,
                "total": 20
            }
        },
        {
            "category": "Biology",
            "scope": "Cell Structure",
            "version": "2.0-db",
            "test_id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210",
            "question_counts": {
                "closed": 25,
                "open": 10,
                "total": 35
            }
        }
    ]
    ```
-   **Error Response (500 Internal Server Error):**
    ```json
    {
        "error": "DB_LIST_ERROR",
        "message": "Server error while fetching test list."
    }
    ```

---

### 2. Get Questions for a Test

-   **Method:** `GET`
-   **Endpoint:** `/questions/`
-   **Description:** Fetches a randomized list of questions for the selected test categories.
-   **Query Parameters:**
    -   `categories` (string, required): A comma-separated list of test UUIDs to draw questions from.
    -   `num_questions` (integer, required): The total number of questions to retrieve.
    -   `mode` (string, optional): The type of questions to fetch. Can be `open`, `closed`, or `mixed` (default).
-   **Success Response (200 OK):**
    ```json
    [
        {
            "id": "c0a80100-0000-4000-8000-000000000101",
            "test_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "questionText": "In which year did the coronation of Bolesław the Brave take place?",
            "image": "https://example.com/link_to_image.png",
            "type": "single-choice",
            "tags": ["rulers", "dates", "Poland"],
            "options": ["1000", "966", "1138", "1025"],
            "correctAnswers": [3],
            "explanation": "The coronation took place in 1025, just before his death.",
            "gradingCriteria": null,
            "maxPoints": null
        }
        // ... more questions
    ]
    ```
-   **Error Responses:**
    -   **400 Bad Request:** If `categories` or `num_questions` are missing or invalid.
        ```json
        {
            "error": "MISSING_PARAMETERS",
            "message": "Parameters 'categories' and 'num_questions' are required."
        }
        ```
    -   **404 Not Found:** If no questions are found for the selected criteria.
        ```json
        {
            "error": "NO_QUESTIONS_FOUND",
            "message": "No questions found for the selected categories in mode 'mixed'."
        }
        ```

---

### 3. Check an Open-Ended Answer

-   **Method:** `POST`
-   **Endpoint:** `/check_answer/`
-   **Description:** Submits an open-ended question answer for asynchronous evaluation. This endpoint loads the rubric (`grading_criteria`, `max_points`, question text, and type) from the question row and enqueues a Celery task. Rate-limited (`ai_grading` throttle).
-   **Request Body:**
    ```json
    {
        "question": "c0a80100-0000-4000-8000-000000000101",
        "userAnswer": "The user's written answer.",
        "forceAI": false
    }
    ```
    -   `question` (UUID, required): primary key of the question to grade.
    -   `userAnswer` (non-empty string, required): the user's written answer.
    -   `forceAI` (bool, optional, default `false`): skip local vector/regex grading and send the answer to the LLM.
    -   `gradingCriteria`, `maxPoints`, `questionType`, and `questionText` in the body are ignored if present; the server uses the stored question row.
-   **Success Response (202 Accepted):**
    ```json
    {
        "task_id": "b4c5d6e7-f8g9-1234-5678-90abcdef1234"
    }
    ```
-   **Error Responses:**
    -   **400 Bad Request** `INCOMPLETE_DATA` — missing `question` or `userAnswer`.
        ```json
        {
            "error": "INCOMPLETE_DATA",
            "message": "Fields 'question' and 'userAnswer' are required."
        }
        ```
    -   **400 Bad Request** `INVALID_PARAMETER_FORMAT` — `question` is not a UUID.
        ```json
        {
            "error": "INVALID_PARAMETER_FORMAT",
            "message": "Field 'question' must be a UUID."
        }
        ```
    -   **404 Not Found** `QUESTION_NOT_FOUND` — no question with that UUID.
        ```json
        {
            "error": "QUESTION_NOT_FOUND",
            "message": "Question not found."
        }
        ```
    -   **400 Bad Request** `INVALID_QUESTION_TYPE` — the question is closed (not open-ended).
        ```json
        {
            "error": "INVALID_QUESTION_TYPE",
            "message": "Only open-ended questions can be graded this way."
        }
        ```
    -   **400 Bad Request** `MISSING_GRADING_CONFIG` — open question is missing grading criteria or `max_points`.
        ```json
        {
            "error": "MISSING_GRADING_CONFIG",
            "message": "This question has no grading criteria or max points."
        }
        ```

---

### 4. Get AI Task Result

-   **Method:** `GET`
-   **Endpoint:** `/task_result/<task_id>/`
-   **Description:** Polls for the result of an asynchronous AI evaluation task.
-   **URL Parameters:**
    -   `task_id` (string, required): The ID of the task returned by the `/check_answer/` endpoint.
-   **Success Response (200 OK):**
    -   If the task is still running:
        ```json
        {
            "status": "PENDING",
            "task_id": "b4c5d6e7-f8g9-1234-5678-90abcdef1234",
            "data": null
        }
        ```
    -   If the task is completed:
        ```json
        {
            "status": "SUCCESS",
            "task_id": "b4c5d6e7-f8g9-1234-5678-90abcdef1234",
            "data": {
                "score": 5,
                "max_points": 6,
                "feedback": "The AI's feedback on the answer.",
                "grading_method": "llm",
                "vector_score": 0.61,
                "latency_ms": 1450
            }
        }
        ```
        `grading_method` is one of `vector_pass`, `vector_fail`, `regex_pass`, `llm`, `fallback_llm`.
    -   If the task failed:
        ```json
        {
            "status": "FAILURE",
            "task_id": "b4c5d6e7-f8g9-1234-5678-90abcdef1234",
            "data": {
                "error": "TASK_FAILED",
                "message": "Grading task failed unexpectedly."
            }
        }
        ```

---

### 5. Report an Issue

-   **Method:** `POST`
-   **Endpoint:** `/report_issue/`
-   **Description:** Submits a report for an issue with a question, answer, or AI evaluation.
-   **Request Body:**
    ```json
    {
        "question": "c0a80100-0000-4000-8000-000000000101",
        "test": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "issue_type": "QUESTION_ERROR",
        "description": "A detailed description of the issue.",
        "ai_feedback_snapshot": "{\"score\": 2, \"feedback\": \"Partial credit.\"}",
        "user_answer_open": "User's text answer for open questions.",
        "user_answer_choices": ["Jupiter"]
    }
    ```
    -   `issue_type` must be `QUESTION_ERROR` or `AI_GRADING_ERROR`.
    -   `ai_feedback_snapshot` is a string (typically `JSON.stringify` of the grading result). Required when `issue_type` is `AI_GRADING_ERROR`.
    -   Open questions (`open-text` / `open-cli` / `open-code`): send `user_answer_open`, leave `user_answer_choices` null.
    -   Closed questions: send `user_answer_choices` as an array of **option text strings** (not integer indices), leave `user_answer_open` null.
-   **Success Response (201 Created):**
    ```json
    {
        "question": "c0a80100-0000-4000-8000-000000000101",
        "test": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "issue_type": "QUESTION_ERROR",
        "description": "A detailed description of the issue.",
        "ai_feedback_snapshot": null,
        "user_answer_open": null,
        "user_answer_choices": ["Jupiter"]
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "description": ["This field may not be blank."],
        "ai_feedback_snapshot": ["AI feedback snapshot is required when reporting a grading error."]
    }
    ```

---

### 6. Register a New User

-   **Method:** `POST`
-   **Endpoint:** `/auth/register/`
-   **Authentication:** None required.
-   **Description:** Creates a new user account and returns an authentication token.
-   **Request Body:**
    ```json
    {
        "username": "john_doe",
        "password": "securepassword123"
    }
    ```
-   **Success Response (201 Created):**
    ```json
    {
        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
        "username": "john_doe"
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "username": ["Username already taken."]
    }
    ```

---

### 7. Log In

-   **Method:** `POST`
-   **Endpoint:** `/auth/login/`
-   **Authentication:** None required.
-   **Description:** Authenticates a user and returns their token.
-   **Request Body:**
    ```json
    {
        "username": "john_doe",
        "password": "securepassword123"
    }
    ```
-   **Success Response (200 OK):**
    ```json
    {
        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
        "username": "john_doe"
    }
    ```
-   **Error Response (401 Unauthorized):**
    ```json
    {
        "error": "INVALID_CREDENTIALS",
        "message": "Invalid username or password."
    }
    ```

---

### 8. Log Out

-   **Method:** `POST`
-   **Endpoint:** `/auth/logout/`
-   **Authentication:** `Token <token>` header required.
-   **Description:** Deletes the user's authentication token, invalidating the session.
-   **Request Body:** None.
-   **Success Response (204 No Content):** empty body.

---

### 9. Start a Quiz Session

-   **Method:** `POST`
-   **Endpoint:** `/sessions/start/`
-   **Authentication:** `Token <token>` header required.
-   **Description:** Creates a new `QuizSession` record for the logged-in user. Called at the start of each quiz.
-   **Request Body:**
    ```json
    {
        "is_study_mode": false
    }
    ```
    *(All fields optional; defaults to `false` for `is_study_mode`.)*
-   **Success Response (201 Created):**
    ```json
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

---

### 10. Complete a Quiz Session

-   **Method:** `POST`
-   **Endpoint:** `/sessions/<session_uuid>/complete/`
-   **Authentication:** `Token <token>` header required.
-   **Description:** Marks a session as completed and records the final totals. The user must own the session.
-   **Request Body:**
    ```json
    {
        "total_questions": 10,
        "correct_count": 7,
        "score_achieved": 8.5,
        "score_possible": 10
    }
    ```
-   **Success Response (200 OK):** empty body.
-   **Error Response (404 Not Found):** the session does not exist or is not owned by the authenticated user.

---

### 11. Submit Question Attempts

-   **Method:** `POST`
-   **Endpoint:** `/attempts/`
-   **Authentication:** `Token <token>` header required.
-   **Description:** Bulk-creates `QuestionAttempt` records for a completed session. If a `difficulty_rating` is provided, the SM-2 algorithm computes the next review schedule for the question.
-   **Request Body (array):**
    ```json
    [
        {
            "question": "c0a80100-0000-4000-8000-000000000101",
            "test": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "session": "550e8400-e29b-41d4-a716-446655440000",
            "is_correct": true,
            "points_awarded": 1,
            "time_spent_secs": 32,
            "difficulty_rating": "normal"
        }
    ]
    ```
    *(`difficulty_rating` is optional; valid values: `"easy"`, `"normal"`, `"hard"`. Mapped to SM-2 quality 5 / 4 / 3. Incorrect answers cap quality at 1 and reset the card. An omitted rating copies the previous SM-2 schedule instead of wiping it.)*
-   **Success Response (201 Created):** empty body.

---

### 12. Get User Statistics

-   **Method:** `GET`
-   **Endpoint:** `/stats/`
-   **Authentication:** `Token <token>` header required.
-   **Description:** Returns aggregated statistics for the authenticated user.
-   **Success Response (200 OK):**
    ```json
    {
        "total_sessions": 12,
        "total_questions_answered": 156,
        "overall_accuracy": 73.4,
        "current_streak_days": 3,
        "longest_streak_days": 7,
        "avg_time_per_question": 28,
        "questions_by_type": { "closed": 120, "open": 36 },
        "study_sessions": 4,
        "regular_sessions": 8,
        "recent_sessions": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "date": "2026-03-27",
                "total_questions": 10,
                "score_achieved": 7,
                "score_possible": 10,
                "accuracy": 70
            }
        ]
    }
    ```
    `recent_sessions` is the 20 most recent completed sessions, newest first.

---

### 13. Get Study Queue

-   **Method:** `GET`
-   **Endpoint:** `/study/queue/`
-   **Authentication:** `Token <token>` header required.
-   **Description:** Returns a mixed list of questions for the Study Mode session. Priority order: (1) questions whose SM-2 review date is today or earlier, (2) recently-wrong questions **not yet scheduled** (`sr_next_review` is null), (3) never-attempted questions from tests the user has studied before. Remaining slots after due cards mix struggling with new; leftover struggling fills any unused slots so the response length matches `limit` when enough cards exist. Cap is `50`.
-   **Query Parameters:**
    -   `limit` (integer, optional): Maximum total questions to return (default `20`, cap `50`).
    -   `test_ids` (string, optional): Comma-separated test UUIDs. Restricts the queue to those tests.
-   **Success Response (200 OK):**
    ```json
    {
        "count": 15,
        "questions": [
            {
                "id": "c0a80100-0000-4000-8000-000000000101",
                "test_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "questionText": "...",
                "type": "single-choice",
                "options": ["A", "B", "C", "D"],
                "correctAnswers": [2],
                "explanation": "...",
                "gradingCriteria": null,
                "maxPoints": null
            }
        ]
    }
    ```

---

### 14. Get Study Queue Stats

-   **Method:** `GET`
-   **Endpoint:** `/study/stats/`
-   **Authentication:** `Token <token>` header required.
-   **Description:** Returns counts used by Study Mode setup (due / struggling / new / mastered) plus the tests the user has already studied. `struggling_count` is unscheduled latest misses only. `total_queued` is `min(due + struggling + new, 50)` and matches what `/study/queue/?limit=50` can return.
-   **Success Response (200 OK):**
    ```json
    {
        "due_count": 8,
        "struggling_count": 3,
        "new_count": 12,
        "mastered_count": 5,
        "total_queued": 20,
        "studied_tests": [
            {
                "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "title": "Medieval Poland"
            }
        ]
    }
    ```

---

### 15. Get Per-Test Statistics

-   **Method:** `GET`
-   **Endpoint:** `/stats/tests/`
-   **Authentication:** `Token <token>` header required.
-   **Description:** Returns per-test attempt aggregates for the authenticated user, ordered by attempt count, capped at 20 tests.
-   **Success Response (200 OK):**
    ```json
    [
        {
            "test_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "title": "Medieval Poland",
            "total_attempts": 40,
            "points_earned": 28,
            "points_possible": 40,
            "accuracy": 70.0,
            "avg_time_secs": 22
        }
    ]
    ```
    `points_possible` is `Sum(Coalesce(question.max_points, 1))` so closed questions without `max_points` count as 1 point each, matching session scoring.

---

## Authoring

Staff-only endpoints for reading, validating, and importing interchange JSON. Every path below is still prefixed with `/api/v1/` and requires `Authorization: Token <token>` plus `is_staff`.

Import **upserts** questions in this order: `question_id` (UUID), then integer `id` (`source_id`), then exact `questionText`. Questions that already have attempts are never deleted if they are omitted from the file; they appear in `questions.blocked_deletes` and `warnings`.

### 16. Get Authoring Schema

-   **Method:** `GET`
-   **Endpoint:** `/authoring/schema/`
-   **Authentication:** Token + `is_staff`.
-   **Description:** Returns the interchange JSON Schema (`schema_version`, `json_schema`, `examples`) used by validate/import.
-   **Success Response (200 OK):** JSON object with `schema_version` (currently `1`), a Draft 2020-12 `json_schema`, and per-type `examples`.

---

### 17. Get Authoring Instructions

-   **Method:** `GET`
-   **Endpoint:** `/authoring/instructions/`
-   **Authentication:** Token + `is_staff`.
-   **Description:** Returns the generic quiz-authoring markdown instructions.
-   **Success Response (200 OK):**
    ```json
    {
        "markdown": "# ..."
    }
    ```

---

### 18. Validate Interchange JSON

-   **Method:** `POST`
-   **Endpoint:** `/authoring/validate/`
-   **Authentication:** Token + `is_staff`.
-   **Description:** Validates a quiz payload without writing to the database. **Always returns 200**, even when the payload is invalid.
-   **Request Body:** Interchange JSON (`category`, `scope`, `questions`, optional `version` / `description` / per-question fields).
-   **Success Response (200 OK):**
    ```json
    {
        "valid": true,
        "errors": []
    }
    ```
    Invalid payload example:
    ```json
    {
        "valid": false,
        "errors": [
            {
                "path": "questions",
                "code": "EMPTY_QUESTIONS",
                "message": "'questions' must not be empty."
            }
        ]
    }
    ```

---

### 19. List Tests (Authoring)

-   **Method:** `GET`
-   **Endpoint:** `/authoring/tests/`
-   **Authentication:** Token + `is_staff`.
-   **Description:** Lists all tests with authoring metadata (includes `description` and `updated_at`, which the public `/tests/` list does not).
-   **Success Response (200 OK):**
    ```json
    [
        {
            "test_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "category": "History",
            "scope": "Medieval Poland",
            "version": "1.0",
            "description": "",
            "question_counts": {
                "closed": 15,
                "open": 5,
                "total": 20
            },
            "updated_at": "2026-08-31T12:00:00+00:00"
        }
    ]
    ```

---

### 20. Export a Test

-   **Method:** `GET`
-   **Endpoint:** `/authoring/tests/<uuid>/export/`
-   **Authentication:** Token + `is_staff`.
-   **Description:** Returns the full interchange JSON for one test. Each question includes both `question_id` (database UUID) and `id` (integer `source_id` from the original file).
-   **Success Response (200 OK):**
    ```json
    {
        "test_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "category": "History",
        "scope": "Medieval Poland",
        "version": "1.0",
        "description": "",
        "questions": [
            {
                "id": 101,
                "question_id": "c0a80100-0000-4000-8000-000000000101",
                "questionText": "In which year did the coronation of Bolesław the Brave take place?",
                "image": "https://example.com/link_to_image.png",
                "type": "single-choice",
                "tags": ["rulers", "dates", "Poland"],
                "explanation": "The coronation took place in 1025, just before his death.",
                "options": ["1000", "966", "1138", "1025"],
                "correctAnswers": [3]
            }
        ]
    }
    ```
-   **Error Response (404 Not Found)** `TEST_NOT_FOUND`.

---

### 21. Get a Single Question

-   **Method:** `GET`
-   **Endpoint:** `/authoring/tests/<uuid>/questions/<uuid>/`
-   **Authentication:** Token + `is_staff`.
-   **Description:** Returns interchange JSON for one question belonging to the given test (`id` = `source_id`, `question_id` = UUID).
-   **Error Responses:**
    -   **404** `TEST_NOT_FOUND` — no test with that UUID.
    -   **404** `QUESTION_NOT_FOUND` — the question UUID is missing or not on that test.

---

### 22. Patch Test Metadata

-   **Method:** `PATCH`
-   **Endpoint:** `/authoring/tests/<uuid>/`
-   **Authentication:** Token + `is_staff`.
-   **Description:** Updates **metadata only**. Accepted fields: `category`, `scope`, `version`, `description`. Question bodies are not edited here; use import for that. Returns the same interchange JSON as export.
-   **Request Body (any subset):**
    ```json
    {
        "category": "Polish History",
        "scope": "Early Piasts",
        "version": "1.1",
        "description": "Updated description."
    }
    ```
-   **Success Response (200 OK):** interchange JSON for the test (includes `questions`).
-   **Error Response (404 Not Found)** `TEST_NOT_FOUND`.

---

### 23. Import a Quiz

-   **Method:** `POST`
-   **Endpoint:** `/authoring/import/`
-   **Authentication:** Token + `is_staff`.
-   **Description:** Creates or updates a test from interchange JSON. Matching order for each question: `question_id`, then integer `id` (`source_id`), then exact `questionText`. Omitted questions without attempts are deleted; omitted questions **with attempts are kept**.
-   **Query / body:**
    -   Optional `test_id` in the JSON body targets an existing test by UUID (otherwise the test is resolved by `scope` title).
    -   Optional `dry_run` as a query parameter (`?dry_run=true`) or a body field. Accepted truthy values: `true`, `1`, `yes`.
-   **Success Response (200 OK):**
    ```json
    {
        "applied": true,
        "dry_run": false,
        "test": {
            "test_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "action": "create",
            "metadata_changes": {
                "scope": {"from": null, "to": "Medieval Poland"}
            }
        },
        "questions": {
            "created": [{"source_id": 101, "questionText": "..."}],
            "updated": [],
            "unchanged": 0,
            "would_delete": [],
            "blocked_deletes": []
        },
        "warnings": [],
        "quiz": {
            "test_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "category": "History",
            "scope": "Medieval Poland",
            "version": "1.0",
            "description": "",
            "questions": []
        }
    }
    ```
    `applied` is `false` when `dry_run` is set (no writes). `quiz` is the interchange snapshot after a real import.
-   **Error Responses:**
    -   **400 Bad Request** `VALIDATION_FAILED` — payload failed schema/content checks (no writes).
        ```json
        {
            "error": "VALIDATION_FAILED",
            "errors": [
                {"path": "questions", "code": "EMPTY_QUESTIONS", "message": "..."}
            ]
        }
        ```
    -   **404 Not Found** `TEST_NOT_FOUND` — `test_id` does not exist.
    -   **409 Conflict** `IMPORT_CONFLICT` — ambiguous title match, or two incoming questions resolved to the same existing row.

---

### Authoring error codes

| Code | HTTP | When |
|---|---|---|
| `AUTHENTICATION_FAILED` | 401 | Missing or invalid token |
| `PERMISSION_DENIED` | 403 | Authenticated but not staff |
| `VALIDATION_FAILED` | 400 | Import payload failed validation |
| `TEST_NOT_FOUND` | 404 | Unknown test UUID |
| `QUESTION_NOT_FOUND` | 404 | Unknown question UUID (or not on that test) |
| `IMPORT_CONFLICT` | 409 | Import could not uniquely match a test or question |

Error bodies are `{ "error": "<CODE>", "message": "..." }` except `VALIDATION_FAILED`, which returns `{ "error": "VALIDATION_FAILED", "errors": [ ... ] }`.
