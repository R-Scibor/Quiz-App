AUTHORING_SCHEMA = {
    "schema_version": 1,
    "json_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["category", "scope", "questions"],
        "additionalProperties": True,
        "properties": {
            "test_id": {"type": "string", "format": "uuid"},
            "category": {"type": "string", "minLength": 1},
            "scope": {"type": "string", "minLength": 1},
            "version": {"type": "string"},
            "description": {"type": "string"},
            "questions": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/question"},
            },
        },
        "$defs": {
            "question": {
                "type": "object",
                "required": ["questionText", "type"],
                "additionalProperties": True,
                "properties": {
                    "id": {"type": ["integer", "null"]},
                    "question_id": {"type": "string", "format": "uuid"},
                    "questionText": {"type": "string", "minLength": 1},
                    "image": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [
                            "single-choice",
                            "multiple-choice",
                            "open-text",
                            "open-cli",
                            "open-code",
                            "open",
                            "open-ended",
                        ],
                    },
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "options": {"type": "array", "minItems": 2, "items": {"type": "string"}},
                    "correctAnswers": {"type": "array", "minItems": 1, "items": {"type": "integer"}},
                    "explanation": {"type": "string"},
                    "gradingCriteria": {"type": "string", "minLength": 1},
                    "maxPoints": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "allOf": [
                    {
                        "if": {"properties": {"type": {"const": "single-choice"}}, "required": ["type"]},
                        "then": {
                            "required": ["options", "correctAnswers"],
                            "properties": {"correctAnswers": {"minItems": 1, "maxItems": 1}},
                        },
                    },
                    {
                        "if": {"properties": {"type": {"const": "multiple-choice"}}, "required": ["type"]},
                        "then": {
                            "required": ["options", "correctAnswers"],
                            "properties": {"correctAnswers": {"minItems": 2}},
                        },
                    },
                    {
                        "if": {
                            "properties": {
                                "type": {"enum": ["open-text", "open-cli", "open-code", "open", "open-ended"]},
                            },
                            "required": ["type"],
                        },
                        "then": {"required": ["gradingCriteria", "maxPoints"]},
                    },
                ],
            },
        },
    },
    "examples": {
        "single-choice": {
            "id": 1,
            "questionText": "...",
            "image": "",
            "type": "single-choice",
            "tags": ["tag1", "tag2"],
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correctAnswers": [2],
            "explanation": "...",
        },
        "multiple-choice": {
            "id": 2,
            "questionText": "Which of the following are true about X? (select all that apply)",
            "image": "",
            "type": "multiple-choice",
            "tags": ["tag1"],
            "options": ["A", "B", "C", "D"],
            "correctAnswers": [0, 2],
            "explanation": "...",
        },
        "open-text": {
            "id": 3,
            "questionText": "...",
            "image": "",
            "type": "open-text",
            "tags": ["tag1"],
            "gradingCriteria": (
                "A natural language description of what a correct answer must contain. "
                "Be specific about required concepts."
            ),
            "maxPoints": 3,
        },
        "open-cli": {
            "id": 4,
            "questionText": "...",
            "image": "",
            "type": "open-cli",
            "tags": ["tag1", "cli"],
            "gradingCriteria": r"command\s+subcommand\s+(flag1|flag2)",
            "maxPoints": 1,
        },
        "open-code": {
            "id": 5,
            "questionText": "...",
            "image": "",
            "type": "open-code",
            "tags": ["tag1", "code"],
            "gradingCriteria": (
                "language: description of what the code must do and what edge cases it must handle"
            ),
            "maxPoints": 3,
        },
    },
}
