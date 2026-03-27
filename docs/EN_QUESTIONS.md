# Guide to Creating and Importing Quizzes

This document provides a complete guide to creating new tests in JSON format and importing them into the "Quiz App" application's database.

---

## 📋 Table of Contents

- [JSON File Structure](#-json-file-structure)
- [Question Object Structure](#-question-object-structure)
  - [Single-Choice Question](#single-choice-question)
  - [Multiple-Choice Question](#multiple-choice-question)
  - [Open-Ended Questions](#open-ended-questions)
    - [open-text — Natural language](#open-text--natural-language)
    - [open-cli — Terminal commands](#open-cli--terminal-commands)
    - [open-code — Programming](#open-code--programming)
- [Markdown & Code Blocks in Question Text](#-markdown--code-blocks-in-question-text)
- [How to Load New Tests into the Database](#-how-to-load-new-tests-into-the-database)

---

## JSON File Structure

Each `.json` file represents one complete test and should have the following main structure:

```json
{
  "category": "Category Name",
  "scope": "Test Name or Scope",
  "version": "1.0",
  "questions": [
    // Array of question objects...
  ]
}
```

-   `category` (string): The main thematic category of the test (e.g., "History", "Biology"). It will be created in the database if it does not already exist.
-   `scope` (string): The title of the test that will be visible to the user (e.g., "Medieval Poland", "Cell Structure").
-   `questions` (array): An array containing all the question objects for the given test.

---

## 📝 Question Object Structure

Each question in the `questions` array is an object with specific fields. Below are examples for each of the supported question types.

### Single-Choice Question

The user can select only one correct answer.

```json
{
  "id": 101,
  "questionText": "In which year did the coronation of Bolesław the Brave take place?",
  "image": "https://example.com/link_to_image.png",
  "type": "single-choice",
  "tags": ["rulers", "dates", "Poland"],
  "options": [
    "966",
    "1000",
    "1025",
    "1138"
  ],
  "correctAnswers": [2],
  "explanation": "The coronation took place in 1025, just before his death."
}
```

-   `id` (integer): A unique identifier for the question within the file (currently unused, but required for consistency).
-   `questionText` (string): The content of the question.
-   `image` (string, optional): A URL link to an image that will be displayed with the question. Can be an empty string `""`.
-   `type` (string): Must be `"single-choice"`.
-   `tags` (array of strings): A list of tags describing the question.
-   `options` (array of strings): A list of possible answers.
-   `correctAnswers` (array of integers): An array containing **one element** - the index (starting from 0) of the correct answer in the `options` array.
-   `explanation` (string, optional): An explanation text that will be displayed to the user after they answer.

### Multiple-Choice Question

The user can select several correct answers.

```json
{
  "id": 202,
  "questionText": "Which of the following elements are found in both prokaryotic and eukaryotic cells?",
  "image": "",
  "type": "multiple-choice",
  "tags": ["cell", "prokaryote", "eukaryote"],
  "options": [
    "Cell membrane",
    "Ribosomes",
    "Mitochondrion",
    "Cell nucleus"
  ],
  "correctAnswers": [0, 1],
  "explanation": "Both prokaryotes and eukaryotes have a cell membrane and ribosomes."
}
```

-   `type` (string): Must be `"multiple-choice"`.
-   `correctAnswers` (array of integers): An array containing the **indices of all correct answers**.

### Open-Ended Questions

The user types a free-text answer. Quiz App supports three open-ended types that use different grading pipelines — see **[GRADING.md](./GRADING.md)** for a full description of how each pipeline works.

> **Deprecated:** The `"open-ended"` type is still accepted for backwards compatibility and is treated as `"open-text"`, but will print a deprecation warning during import. Use `"open-text"` in new files.

All open-ended types share these fields and omit `options` / `correctAnswers`:

| Field | Required | Description |
|---|---|---|
| `gradingCriteria` | Yes | Grading rules — content depends on the type (see below) |
| `maxPoints` | Yes | Integer 1–100. Points awarded can be a fraction of this. |

---

#### `open-text` — Natural language

Use for explanations, definitions, and descriptive answers. Graded by vector similarity first; ambiguous answers escalate to Gemini.

**`gradingCriteria`:** A natural language description of what a correct answer must contain. This text is used as the semantic comparison baseline.

```json
{
  "id": 104,
  "questionText": "List and briefly describe at least three consequences of the Congress of Gniezno in 1000.",
  "image": "",
  "type": "open-text",
  "tags": ["congress of gniezno", "diplomacy"],
  "gradingCriteria": "The answer must include at least three of the following: establishment of an independent Polish church province, strengthening of Poland's international position, symbolic recognition of the state's sovereignty by the Empire.",
  "maxPoints": 6
}
```

---

#### `open-cli` — Terminal commands

Use for questions that expect a shell command (`kubectl`, `git`, `docker`, `bash`, etc.). Graded by regex match; unmatched answers escalate to Gemini with a prompt that rejects destructive flags.

**`gradingCriteria`:** A Python-compatible regex pattern matched against the full answer. Backslashes must be doubled in JSON (`\\s+` → `\s+` at runtime). The regex is validated at import time.

```json
{
  "id": 105,
  "questionText": "Write a command to list all pods in the kube-system namespace.",
  "image": "",
  "type": "open-cli",
  "tags": ["kubernetes", "cli"],
  "gradingCriteria": "kubectl\\s+get\\s+(pods|po)(\\s+(-n\\s+|--namespace(=|\\s+))kube-system|\\s+(--all-namespaces|-A))?",
  "maxPoints": 1
}
```

**Regex tips:**
- `re.fullmatch` is used — the pattern must match the entire answer, not just a substring. No need for `^` / `$`.
- `re.IGNORECASE` is applied automatically.
- Use `(a|b)` for alternatives, `\\s+` for whitespace.
- Keep patterns readable — Gemini handles edge cases the regex misses.
- The import command rejects patterns with catastrophic backtracking heuristics (nested quantifiers like `(a+)+`).

---

#### `open-code` — Programming

Use for questions that expect code (functions, algorithms, scripts). Always graded by Gemini with a code-specific rubric — partial credit is awarded for partially correct logic.

**`gradingCriteria`:** Must start with a language identifier followed by a colon, then a description of what the code must do.

```json
{
  "id": 210,
  "questionText": "Write a Python function called `add` that takes two numbers and returns their sum.",
  "image": "",
  "type": "open-code",
  "tags": ["python", "functions"],
  "gradingCriteria": "python: function named 'add' that accepts two numeric arguments and returns their sum; must handle integers and floats",
  "maxPoints": 3
}
```

Supported language identifiers: `python`, `javascript`, `go`, `bash`, `java`, `sql`, `typescript`, `rust`, `c`, `cpp`, or any language Gemini recognizes.

---

## 📝 Markdown & Code Blocks in Question Text

The `questionText` and `explanation` fields support **Markdown**, including syntax-highlighted code blocks. However, because JSON strings cannot contain literal newlines, every line break must be written as `\n` (a backslash followed by `n`).

### The golden rule

> Write your Markdown as a single JSON string, replacing every line break with `\n`.

### Syntax-highlighted code block

To get syntax highlighting, specify the language after the opening triple-backtick fence.

```json
"questionText": "What does the following YAML configure?\n\n```yaml\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: my-app\nspec:\n  replicas: 3\n```"
```

**Supported language identifiers** (Prism): `yaml`, `bash`, `python`, `javascript`, `json`, `sql`, `dockerfile`, `go`, `java`, `css`, `html`, `nginx`, `toml`, and [many more](https://prismjs.com/#supported-languages).

### Code block without syntax highlighting

Omit the language identifier for a plain monospace block:

```json
"questionText": "What does this output?\n\n```\nHello, World!\n```"
```

### Inline code

Use single backticks for short inline code snippets:

```json
"questionText": "What flag does `kubectl get pods` use to filter by namespace?"
```

### Escaping backslashes

Inside a JSON string, a literal backslash must be written as `\\`. This matters for regex patterns, Windows paths, and escape sequences in code examples:

```json
"questionText": "What does `\\n` represent in Python strings?"
```

The rendered text will show `\n`.

### Common mistakes to avoid

| Mistake | Problem | Fix |
|---------|---------|-----|
| Literal newline inside the JSON string | Invalid JSON — file fails to import | Replace each newline with `\n` |
| Opening fence and first code line on the same line (` ```yaml key: value `) | First line is treated as the info string, not code | Put the first code line on its own `\n` after the fence |
| Missing closing fence (` ``` `) | Block is unclosed; everything after renders as code | Always close with ` ``` ` on its own line via `\n` |
| No language after fence for YAML/CLI questions | Renders as plain text without highlighting | Add the language: ` ```yaml `, ` ```bash `, etc. |

---

**IMPORTANT:** Before uploading tests to the database, it is recommended to use the `validate_quiz_json` command to ensure the files are correct and do not contain errors.

**Example usage:**

```bash
python manage.py validate_quiz_json media/tests/my_quiz.json
```

**Example usage (inside the container):**

```bash
docker compose exec web python manage.py validate_quiz_json media/tests/my_quiz.json
```

## 🚀 How to Load New Tests into the Database

The following instructions describe the process of adding new `.json` test files to the application running in Docker containers on a virtual machine (VM).

### Step 1: Prepare the files on your computer (PC)

1.  **Create new test files**: Prepare your new tests in `.json` format.
2.  **Place them in the appropriate folder**: On your local computer, place all new `.json` files in the `media/tests/` folder in the main project directory.

### Step 2: Import the tests into the application (in Docker)

Once the files are on the server, we need to tell Django to read them and add them to the database.

1.  **Connect to the VM server**: Make sure you have a terminal open connected to your virtual machine.
2.  **Run the import command**: Execute the following command. It runs inside the `web` container and points to the folder where you just sent the files.

    ```bash
    docker compose exec web python manage.py import_quizzes media/tests
    ```
    **Importing a single file:**
    You can also load a single JSON file by providing a direct path to it:
    ```bash
    docker compose exec web python manage.py import_quizzes media/tests/my_new_quiz.json
    ```
    **Clearing the database:**
    If you want to completely clear the database and import everything from scratch, use the `--clean` flag:
    ```bash
    docker compose exec web python manage.py import_quizzes media/tests --clean
    ```

3.  **Done!** Your new tests should now be visible in the application.