# Guide to Creating and Importing Quizzes

This document provides a complete guide to creating new tests in JSON format and importing them into the "Quiz App" application's database.

---

## 📋 Table of Contents

- [JSON File Structure](#-json-file-structure)
- [Question Object Structure](#-question-object-structure)
  - [Single-Choice Question](#single-choice-question)
  - [Multiple-Choice Question](#multiple-choice-question)
  - [Open-Ended Question](#open-ended-question)
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

### Open-Ended Question

The user must type a text answer, which is evaluated by an AI.

```json
{
  "id": 104,
  "questionText": "List and briefly describe at least three consequences of the Congress of Gniezno in 1000.",
  "image": "",
  "type": "open-ended",
  "tags": ["congress of gniezno", "diplomacy"],
  "gradingCriteria": "The answer must include at least three of the following consequences, with a brief explanation: 1. Establishment of an independent Polish church province. 2. Strengthening of Poland's international position. 3. Symbolic recognition of the state's sovereignty by the Empire.",
  "maxPoints": 6
}
```

-   `type` (string): Must be `"open-ended"`.
-   `gradingCriteria` (string): **A key field.** A detailed description based on which the AI will evaluate the user's answer. It should be precise and clearly state what is required.
-   `maxPoints` (integer): The maximum number of points that can be awarded for this question.
-   The `options` and `correctAnswers` fields **must be omitted**.

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