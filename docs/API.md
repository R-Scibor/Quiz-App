# API Documentation

This document provides a detailed description of the API endpoints available in the Quiz App.

---

## Base URL

All API endpoints are prefixed with `/api/v1/`.

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
        "message": "A server error occurred while fetching the list of tests."
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
            "id": 101,
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
            "message": "No questions found for the selected categories in 'mixed' mode."
        }
        ```

---

### 3. Check an Open-Ended Answer

-   **Method:** `POST`
-   **Endpoint:** `/check_answer/`
-   **Description:** Submits an open-ended question answer for asynchronous evaluation by the AI. This endpoint initiates a background task.
-   **Request Body:**
    ```json
    {
        "userAnswer": "The user's written answer.",
        "gradingCriteria": "The criteria from the question object.",
        "questionText": "The text of the question.",
        "maxPoints": 6
    }
    ```
-   **Success Response (202 Accepted):**
    ```json
    {
        "task_id": "b4c5d6e7-f8g9-1234-5678-90abcdef1234"
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "error": "INCOMPLETE_DATA",
        "message": "Missing all required fields."
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
                "evaluation": "The AI's feedback on the answer.",
                "points": 5
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
        "question": "question_uuid",
        "test": "test_uuid",
        "issue_type": "INCORRECT_QUESTION", // or "INCORRECT_ANSWER", "AI_GRADING_ERROR"
        "description": "A detailed description of the issue.",
        "ai_feedback_snapshot": { "evaluation": "...", "points": "..." }, // Required if issue_type is "AI_GRADING_ERROR"
        "user_answer_open": "User's text answer for open questions.",
        "user_answer_choices": { "selected": [1, 3] } // User's selected options for closed questions.
    }
    ```
-   **Success Response (201 Created):**
    ```json
    {
        "question": "question_uuid",
        "test": "test_uuid",
        "issue_type": "INCORRECT_QUESTION",
        "description": "A detailed description of the issue.",
        // ... other fields
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "description": ["This field may not be blank."],
        "ai_feedback_snapshot": ["AI feedback snapshot is required when reporting a grading error."]
    }