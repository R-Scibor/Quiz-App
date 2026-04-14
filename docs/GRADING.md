# Cascade Grading System

This document describes how open-ended questions are graded in Quiz App and how to configure each grading path.

---

## Overview

Instead of sending every open-ended answer to an LLM, Quiz App uses a **cascade**: fast, cheap local methods run first and only escalate to the LLM when they can't give a confident result.

```
User answer
    │
    ▼
open-text ──► Vector similarity ──► score ≥ 0.85 → Auto-Pass  (instant)
                                 ├── score ≤ 0.30 → Auto-Fail  (instant)
                                 └── 0.30–0.85   → LLM (Gemini or Vertex AI)

open-cli  ──► Regex match ──► match   → Auto-Pass  (instant)
                          └── no match → LLM (Gemini or Vertex AI)

open-code ──────────────────────────────► LLM (Gemini or Vertex AI, always)
```

**Expected LLM call reduction:**
- `open-cli` — ~95% graded locally (regex match)
- `open-text` — ~40–60% graded locally (vector thresholds)
- `open-code` — always LLM (semantic similarity doesn't work for code correctness)

---

## Question Types

### `open-text`

Natural language answers — explanations, descriptions, definitions.

**Grading pipeline:**
1. Both the student answer and the `gradingCriteria` text are sanitized (HTML stripped, whitespace collapsed, unicode normalized).
2. Both are embedded by the vector microservice using `all-MiniLM-L6-v2`.
3. Cosine similarity is computed:
   - **≥ 0.85** → Auto-Pass: full points, feedback `"Correct — strong semantic match."`
   - **≤ 0.30** → Auto-Fail: 0 points, feedback `"Incorrect — answer does not match expected meaning."`
   - **0.30–0.85** → Escalated to the active LLM with the standard `PromptConfiguration` template.
4. If the vector microservice is unreachable, falls back to the LLM directly (`grading_method: "fallback_llm"`).

**`gradingCriteria` field:** Write a natural language description of a correct answer. This text is used both as the vector comparison baseline and as the Gemini rubric.

```json
{
  "type": "open-text",
  "gradingCriteria": "A process is an instance of a running program. It has its own PID, memory space, and CPU time allocated by the OS kernel.",
  "maxPoints": 3
}
```

---

### `open-cli`

Terminal commands — `kubectl`, `git`, `docker`, `bash`, etc.

**Grading pipeline:**
1. The student answer is sanitized (leading/trailing whitespace stripped, internal spaces collapsed to one).
2. `re.fullmatch(gradingCriteria, normalized_answer, re.IGNORECASE)` is evaluated.
3. **Match** → Auto-Pass: full points.
4. **No match** → Escalated to the active LLM with a CLI-specific prompt that explicitly rejects destructive flags (`--force`, `-f` with `rm`, `--delete`, etc.).

**`gradingCriteria` field:** A Python-compatible regex pattern. The pattern is matched against the full answer (not a substring search). JSON requires backslashes to be doubled.

```json
{
  "type": "open-cli",
  "gradingCriteria": "kubectl\\s+get\\s+(pods|po)(\\s+(-n\\s+|--namespace(=|\\s+))kube-system|\\s+(--all-namespaces|-A))?",
  "maxPoints": 1
}
```

**Regex validation at import time:** The `import_quizzes` command validates all `open-cli` regex patterns before inserting them into the database:
- Invalid syntax → import fails with an error message.
- Patterns with catastrophic backtracking heuristics (e.g. `(a+)+`) → rejected.
- Evaluation is capped at 1 second.

**Regex tips:**
- Use `\\s+` (doubled backslash in JSON) for one-or-more whitespace.
- Use `(a|b)` for alternatives.
- `re.fullmatch` anchors the entire string — no need for `^` / `$`.
- Keep patterns readable — Gemini handles the edge cases you don't cover.

---

### `open-code`

Programming logic — functions, algorithms, scripts.

**Grading pipeline:**
1. Always sent to the active LLM with a code-specific prompt:
   - Language is parsed from the `gradingCriteria` prefix (e.g. `python: ...`).
   - Prompt instructs the model to evaluate correctness, not style, and to award partial credit.

**`gradingCriteria` field:** Must start with a language identifier followed by a colon, then a description of requirements.

```json
{
  "type": "open-code",
  "gradingCriteria": "python: function named 'add' that accepts two numeric arguments and returns their sum; must handle integers and floats",
  "maxPoints": 3
}
```

Supported language identifiers: any string that Gemini recognizes (e.g. `python`, `javascript`, `go`, `bash`, `java`, `sql`).

> **Note:** The `gradingCriteria` field is required for all open types. Import will fail if it is missing or (for `open-code`) if the language prefix is absent.

---

## Grading Method Field

Every grading result includes a `grading_method` field in the Celery task result. This is used by the frontend to show the **"Auto-graded"** or **"Graded by AI"** badge, and can be used for future cost analysis.

| Value | Meaning |
|---|---|
| `vector_pass` | Cosine similarity ≥ 0.85 → auto-pass |
| `vector_fail` | Cosine similarity ≤ 0.30 → auto-fail |
| `regex_pass` | Regex matched → auto-pass |
| `exact_pass` | Reserved for future exact-match path |
| `llm` | LLM used (score was in ambiguous range, or no local method matched) |
| `fallback_llm` | Vector service was unreachable; Gemini used as fallback |

---

## LLM Provider

The active LLM gateway is controlled by the `LLM_PROVIDER` environment variable. Both `web` and `celery` must see the same value.

| `LLM_PROVIDER` | Authentication | Required env vars |
|---|---|---|
| `gemini` *(default)* | Direct API key | `GEMINI_API_KEY` |
| `vertex` | GCP service account | `VERTEX_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` |

### Switching to Vertex AI

1. Create `secrets/` at the project root and place your service-account JSON key there as `vertex-sa-key.json`:
   ```
   Quiz-App/
   └── secrets/
       └── vertex-sa-key.json   ← never commit this file
   ```
   > The `docker-compose.yml` mounts it read-only at `/run/secrets/vertex-sa-key.json` inside `web` and `celery`.

2. Add to `.env`:
   ```env
   LLM_PROVIDER=vertex
   VERTEX_PROJECT_ID=your-gcp-project-id
   VERTEX_LOCATION=us-central1      # optional, default: us-central1
   VERTEX_MODEL=gemini-2.5-flash    # optional, default: gemini-2.5-flash
   ```

3. Rebuild and restart:
   ```bash
   docker compose up --build -d
   ```

To revert to the direct Gemini API key, set `LLM_PROVIDER=gemini` (or remove the variable).

---

## Vector Microservice (`ai_grader`)

The vector similarity service runs as a separate Docker container to avoid loading PyTorch into the Django/Celery workers.

**Service:** `ai_grader` on port `8001` (internal network only, not exposed to the host).

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status": "ready"}` (HTTP 200) once the model is loaded. Returns 503 while loading. |
| `POST` | `/compare` | Computes cosine similarity between two texts. |

**`POST /compare` request:**
```json
{
  "student_answer": "Paris",
  "reference_answer": "The capital of France is Paris."
}
```

**`POST /compare` response:**
```json
{
  "similarity_score": 0.7253,
  "cached": false
}
```

**Model:** `all-MiniLM-L6-v2` (sentence-transformers, CPU). Pre-downloaded at image build time. LRU cache (128 entries) avoids re-embedding identical texts.

**Offline mode:** The Dockerfile sets `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` so the container never contacts HuggingFace at runtime. All model files are baked into the image — no network access is required after the initial `docker compose build`.

**Resource limits:** 1 CPU, 512 MB RAM (set in `docker-compose.yml`).

**Startup:** The Celery worker depends on the `ai_grader` healthcheck passing before it starts, so no grading requests are sent while the model is still loading (~15–30s on first start after a cold pull).

---

## Thresholds

The vector thresholds (0.85 pass / 0.30 fail) are starting values. After collecting real answer pairs you should tune them:

1. Run a batch of student answers through `/compare` and log `similarity_score` alongside human-graded correct/incorrect labels.
2. Plot the distribution and find the score range where most errors occur.
3. Update `VECTOR_PASS_THRESHOLD` and `VECTOR_FAIL_THRESHOLD` in `api_v1/tasks.py`.

A per-question threshold override field is planned for v0.3.

---

## Legacy Type

The `open-ended` type is recognized by the import command and treated as `open-text` with a deprecation warning. All existing questions in the database were migrated to `open-text` automatically via migration `0006`. **Do not use `open-ended` in new JSON files.**
