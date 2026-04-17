import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique UUID identifier for the category.")
    name = models.CharField(max_length=255, unique=True, help_text="Category name.")
    description = models.TextField(blank=True, null=True, help_text="Optional category description.")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique UUID identifier for the tag.")
    name = models.CharField(max_length=100, unique=True, help_text="Tag name.")

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

    def __str__(self):
        return self.name

class Test(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique UUID identifier for the test.")
    title = models.CharField(max_length=255, help_text="Test title.")
    description = models.TextField(blank=True, null=True, help_text="Optional test description.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time the test was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time of last update.")
    categories = models.ManyToManyField(Category, related_name="tests", blank=True, help_text="Categories this test belongs to.")

    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Tests"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Question(models.Model):
    SINGLE_CHOICE = 'single-choice'
    MULTIPLE_CHOICE = 'multiple-choice'
    OPEN_ENDED = 'open-ended'   # legacy alias — migrated to open-text
    OPEN_TEXT = 'open-text'
    OPEN_CLI = 'open-cli'
    OPEN_CODE = 'open-code'

    QUESTION_TYPE_CHOICES = [
        (SINGLE_CHOICE, 'Single choice'),
        (MULTIPLE_CHOICE, 'Multiple choice'),
        (OPEN_TEXT, 'Open (text)'),
        (OPEN_CLI, 'Open (CLI command)'),
        (OPEN_CODE, 'Open (code)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique UUID identifier for the question.")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions", help_text="Test this question belongs to.")
    text = models.TextField(help_text="Question text.")
    image = models.URLField(max_length=1024, blank=True, null=True, help_text="Optional URL to an image associated with the question.")

    explanation = models.TextField(blank=True, null=True, help_text="Optional explanation of the correct answer.")

    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default=SINGLE_CHOICE,
        help_text="Question type (single choice, multiple choice, open)."
    )

    grading_criteria = models.TextField(
        blank=True, null=True,
        help_text="Grading criteria for open questions."
    )
    max_points = models.PositiveIntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Maximum points for open questions (1–100)."
    )

    tags = models.ManyToManyField(Tag, related_name="questions", blank=True, help_text="Tags associated with this question.")

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['id']
        indexes = [models.Index(fields=['test'], name='question_test_id_idx')]
        constraints = [models.UniqueConstraint(fields=['test', 'text'], name='unique_question_text_in_test')]

    def __str__(self):
        return f"{self.text[:80]}..." if len(self.text) > 80 else self.text

class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique UUID identifier for the answer.")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers", help_text="Question this answer belongs to.")
    text = models.CharField(max_length=1024, help_text="Answer text.")
    is_correct = models.BooleanField(default=False, help_text="Whether this answer is correct.")

    class Meta:
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        ordering = ['id']
        indexes = [models.Index(fields=['question'], name='answer_question_id_idx')]
        constraints = [models.UniqueConstraint(fields=['question', 'text'], name='unique_answer_text_for_question')]

    def __str__(self):
        return f"{self.text[:80]}..." if len(self.text) > 80 else self.text



class ReportedIssue(models.Model):
    """Stores user-submitted reports for question errors or incorrect AI grading."""
    ISSUE_TYPE_CHOICES = [
        ('QUESTION_ERROR', 'Error in question/answer'),
        ('AI_GRADING_ERROR', 'Incorrect AI grading'),
    ]

    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('IN_PROGRESS', 'In progress'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="reported_issues", help_text="Question this report relates to.")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="reported_issues", help_text="Test in which the issue occurred.")

    issue_type = models.CharField(
        max_length=20,
        choices=ISSUE_TYPE_CHOICES,
        help_text="Type of reported issue."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of the issue from the user."
    )
    ai_feedback_snapshot = models.TextField(
        blank=True,
        null=True,
        help_text="Saved AI response at the time of the report (for AI_GRADING_ERROR reports)."
    )
    user_answer_open = models.TextField(
        blank=True,
        null=True,
        help_text="User's answer for open questions."
    )
    user_answer_choices = models.JSONField(
        blank=True,
        null=True,
        help_text="User's selected options for closed questions (stored as a list of strings)."
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW',
        help_text="Current status of the report."
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time the report was created.")

    class Meta:
        verbose_name = "Reported Issue"
        verbose_name_plural = "Reported Issues"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['question'], name='reported_issue_question_idx'),
            models.Index(fields=['test'], name='reported_issue_test_idx'),
            models.Index(fields=['status'], name='reported_issue_status_idx'),
        ]

    def __str__(self):
        return f"Report {self.id} for question {self.question.id}"


class PromptConfiguration(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Unique prompt name, e.g. 'default_grading_prompt'.")
    prompt_text = models.TextField(help_text="Prompt template. Use {variables} for dynamic data.")
    is_active = models.BooleanField(default=True, help_text="Whether this prompt is currently active.")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Prompt Configuration"
        verbose_name_plural = "Prompt Configurations"


class QuizSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    score_achieved = models.FloatField(default=0)
    score_possible = models.FloatField(default=0)
    is_study_mode = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=['user', 'started_at'])]
        ordering = ['-started_at']

    def __str__(self):
        return f"Session {self.id} by {self.user}"


class QuestionAttempt(models.Model):
    DIFFICULTY_EASY = 'easy'
    DIFFICULTY_NORMAL = 'normal'
    DIFFICULTY_HARD = 'hard'
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('normal', 'Normal'),
        ('hard', 'Hard'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='question_attempts')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='attempts')

    is_correct = models.BooleanField()
    points_awarded = models.FloatField(default=0)
    time_spent_secs = models.PositiveIntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    # Spaced repetition fields (populated when user rates difficulty)
    difficulty_rating = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, null=True, blank=True)
    sr_interval = models.PositiveIntegerField(default=1)
    sr_ease_factor = models.FloatField(default=2.5)
    sr_next_review = models.DateField(null=True, blank=True)
    sr_repetitions = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'question']),
            models.Index(fields=['user', 'sr_next_review']),
            models.Index(fields=['session']),
            models.Index(fields=['answered_at']),
        ]

    def __str__(self):
        return f"Attempt by {self.user} on question {self.question_id}"
