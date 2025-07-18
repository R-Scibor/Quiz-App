import uuid
from django.db import models

# -----------------------------------------------------------------------------
# Poniższe modele definiują strukturę bazy danych dla aplikacji Quiz App.
# Zgodnie z planem migracji, implementacja uwzględnia najlepsze praktyki:
#
# 1.  **UUID jako klucze główne**: Każdy model używa `UUIDField` jako klucza
#     głównego (`id`). Zapewnia to globalną unikalność identyfikatorów,
#     utrudnia odgadywanie adresów URL i ułatwia przyszłą replikację
#     lub integrację z innymi systemami.
#
# 2.  **Jawne Indeksy**: W klasie `Meta` każdego modelu, który posiada
#     klucz obcy, zdefiniowano indeksy (`models.Index`). Przyspiesza to
#     znacząco operacje filtrowania i łączenia tabel (JOIN), co jest
#     kluczowe dla wydajności aplikacji przy dużej ilości danych.
#
# 3.  **Ograniczenia Integralności (Constraints)**: Używamy `Meta.constraints`,
#     aby zapewnić spójność danych na poziomie bazy danych. Jest to bardziej
#     niezawodne niż walidacja na poziomie aplikacji, ponieważ działa
#     niezależnie od sposobu zapisu danych.
#
# 4.  **Czytelne `related_name`**: W relacjach `ForeignKey` i `ManyToManyField`
#     stosujemy `related_name`, aby ułatwić odpytywanie bazy danych
#     w "odwrotnym" kierunku (np. od Testu do jego Pytań).
#
# -----------------------------------------------------------------------------


import uuid
from django.db import models

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unikalny identyfikator UUID dla kategorii.")
    name = models.CharField(max_length=255, unique=True, help_text="Nazwa kategorii.")
    description = models.TextField(blank=True, null=True, help_text="Opcjonalny opis kategorii.")

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        ordering = ['name']

    def __str__(self):
        return self.name

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unikalny identyfikator UUID dla tagu.")
    name = models.CharField(max_length=100, unique=True, help_text="Nazwa tagu.")

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tagi"
        ordering = ['name']

    def __str__(self):
        return self.name

class Test(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unikalny identyfikator UUID dla testu.")
    title = models.CharField(max_length=255, help_text="Tytuł testu.")
    description = models.TextField(blank=True, null=True, help_text="Opcjonalny opis testu.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Data i czas utworzenia testu.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Data i czas ostatniej aktualizacji testu.")
    categories = models.ManyToManyField(Category, related_name="tests", blank=True, help_text="Kategorie, do których należy test.")

    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Testy"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Question(models.Model):
    SINGLE_CHOICE = 'single-choice'
    MULTIPLE_CHOICE = 'multiple-choice'
    OPEN_ENDED = 'open-ended'
    
    QUESTION_TYPE_CHOICES = [
        (SINGLE_CHOICE, 'Jednokrotnego wyboru'),
        (MULTIPLE_CHOICE, 'Wielokrotnego wyboru'),
        (OPEN_ENDED, 'Otwarte'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unikalny identyfikator UUID dla pytania.")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions", help_text="Test, do którego przypisane jest to pytanie.")
    text = models.TextField(help_text="Treść pytania.")
    image = models.URLField(max_length=1024, blank=True, null=True, help_text="Opcjonalny link URL do obrazka powiązanego z pytaniem.")

    explanation = models.TextField(blank=True, null=True, help_text="Opcjonalne wyjaśnienie poprawnej odpowiedzi.")
    
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default=SINGLE_CHOICE,
        help_text="Typ pytania (jednokrotnego wyboru, wielokrotnego wyboru, otwarte)."
    )

    grading_criteria = models.TextField(
        blank=True, null=True, 
        help_text="Kryteria oceny dla pytań otwartych."
    )
    max_points = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Maksymalna liczba punktów dla pytań otwartych."
    )

    tags = models.ManyToManyField(Tag, related_name="questions", blank=True, help_text="Tagi powiązane z pytaniem.")

    class Meta:
        verbose_name = "Pytanie"
        verbose_name_plural = "Pytania"
        ordering = ['id']
        indexes = [models.Index(fields=['test'], name='question_test_id_idx')]
        constraints = [models.UniqueConstraint(fields=['test', 'text'], name='unique_question_text_in_test')]

    def __str__(self):
        return f"{self.text[:80]}..." if len(self.text) > 80 else self.text

class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unikalny identyfikator UUID dla odpowiedzi.")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers", help_text="Pytanie, do którego przypisana jest ta odpowiedź.")
    text = models.CharField(max_length=1024, help_text="Treść odpowiedzi.")
    is_correct = models.BooleanField(default=False, help_text="Czy ta odpowiedź jest poprawna?")

    class Meta:
        verbose_name = "Odpowiedź"
        verbose_name_plural = "Odpowiedzi"
        ordering = ['id']
        indexes = [models.Index(fields=['question'], name='answer_question_id_idx')]
        constraints = [models.UniqueConstraint(fields=['question', 'text'], name='unique_answer_text_for_question')]

    def __str__(self):
        return f"{self.text[:80]}..." if len(self.text) > 80 else self.text



class ReportedIssue(models.Model):
    """
    Model do przechowywania zgłoszeń dotyczących pytań lub ocen AI.
    """
    ISSUE_TYPE_CHOICES = [
        ('QUESTION_ERROR', 'Błąd w pytaniu/odpowiedzi'),
        ('AI_GRADING_ERROR', 'Niesłuszna ocena AI'),
    ]

    STATUS_CHOICES = [
        ('NEW', 'Nowe'),
        ('IN_PROGRESS', 'W trakcie analizy'),
        ('RESOLVED', 'Rozwiązane'),
        ('REJECTED', 'Odrzucone'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="reported_issues", help_text="Pytanie, którego dotyczy zgłoszenie.")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="reported_issues", help_text="Test, w którym wystąpiło zgłoszenie.")
    
    issue_type = models.CharField(
        max_length=20,
        choices=ISSUE_TYPE_CHOICES,
        help_text="Typ zgłoszonego problemu."
    )
    description = models.TextField(
        blank=True, 
        null=True, 
        help_text="Opcjonalny opis problemu od użytkownika."
    )
    ai_feedback_snapshot = models.TextField(
        blank=True, 
        null=True, 
        help_text="Zapisana odpowiedź AI w momencie zgłoszenia (dla zgłoszeń typu 'AI_GRADING_ERROR')."
    )
    user_answer_open = models.TextField(
        blank=True,
        null=True,
        help_text="Odpowiedź użytkownika dla pytań otwartych."
    )
    user_answer_choices = models.JSONField(
        blank=True,
        null=True,
        help_text="Zaznaczone opcje przez użytkownika dla pytań zamkniętych (przechowywane jako lista tekstów)."
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW',
        help_text="Aktualny status zgłoszenia."
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Data i czas utworzenia zgłoszenia.")

    class Meta:
        verbose_name = "Zgłoszony Problem"
        verbose_name_plural = "Zgłoszone Problemy"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['question'], name='reported_issue_question_idx'),
            models.Index(fields=['test'], name='reported_issue_test_idx'),
            models.Index(fields=['status'], name='reported_issue_status_idx'),
        ]

    def __str__(self):
        return f"Zgłoszenie {self.id} dla pytania {self.question.id}"
