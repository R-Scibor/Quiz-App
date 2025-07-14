from django.contrib import admin
from .models import Test, Question, Answer, Category, Tag, ReportedIssue

# -----------------------------------------------------------------------------
# Konfiguracja Panelu Administracyjnego
# -----------------------------------------------------------------------------
#
# Poniższy kod konfiguruje panel administracyjny Django, aby w wygodny
# i przejrzysty sposób zarządzać danymi aplikacji Quiz.
#
# Główne ulepszenia:
#
# 1.  **Inlines (elementy osadzone)**:
#     - Odpowiedzi (`Answer`) są wyświetlane i edytowalne bezpośrednio na
#       stronie edycji Pytania (`Question`).
#     - Pytania (`Question`) są widoczne na stronie edycji Testu (`Test`).
#     To eliminuje potrzebę przechodzenia między różnymi stronami i daje
#     pełen obraz danych w jednym miejscu.
#
# 2.  **list_display**:
#     - Dostosowuje kolumny widoczne na listach obiektów, pokazując
#       najważniejsze informacje (np. tytuł testu, typ pytania, treść).
#
# 3.  **list_filter**:
#     - Dodaje panel filtrowania po prawej stronie, umożliwiając szybkie
#       filtrowanie obiektów np. po kategorii, tagach czy typie pytania.
#
# 4.  **search_fields**:
#     - Wprowadza pole wyszukiwania, które pozwala na przeszukiwanie
#       konkretnych pól tekstowych (np. tytułu testu, treści pytania).
#
# 5.  **filter_horizontal**:
#     - Zmienia domyślny widget dla pól ManyToMany (np. tagi, kategorie)
#       na bardziej przyjazny interfejs z dwoma okienkami.
#
# -----------------------------------------------------------------------------


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Konfiguracja panelu admina dla modelu Category."""
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Konfiguracja panelu admina dla modelu Tag."""
    search_fields = ('name',)


class AnswerInline(admin.TabularInline):
    """Umożliwia edycję odpowiedzi bezpośrednio na stronie pytania."""
    model = Answer
    extra = 1  # Domyślnie pokazuj jedno dodatkowe pole na nową odpowiedź
    fields = ('text', 'is_correct')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Konfiguracja panelu admina dla modelu Question."""
    list_display = ('text', 'test', 'question_type')
    list_filter = ('question_type', 'test__categories', 'tags')
    search_fields = ('text', 'explanation')
    filter_horizontal = ('tags',)
    inlines = [AnswerInline] # Osadź formularz odpowiedzi w pytaniu

    fieldsets = (
        (None, {
            'fields': ('test', 'text', 'tags')
        }),
        ('Szczegóły Pytania', {
            'classes': ('collapse',), # Domyślnie zwinięta sekcja
            'fields': ('question_type', 'explanation')
        }),
        ('Pytania Otwarte (Opcjonalne)', {
            'classes': ('collapse',),
            'fields': ('grading_criteria', 'max_points')
        }),
    )


class QuestionInline(admin.StackedInline):
    """Umożliwia podgląd pytań na stronie testu (tylko do odczytu)."""
    model = Question
    extra = 0 # Nie pokazuj dodatkowych pustych pól
    show_change_link = True # Link do edycji każdego pytania
    readonly_fields = ('text', 'question_type')
    can_delete = False
    
    # Wykluczamy pola, których nie chcemy tu widzieć
    exclude = ('explanation', 'grading_criteria', 'max_points', 'tags')


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Konfiguracja panelu admina dla modelu Test."""
    list_display = ('title', 'get_categories', 'created_at')
    # <--- POPRAWKA: Usunięto 'tags' z list_filter, bo nie ma go w modelu Test
    list_filter = ('categories',)
    search_fields = ('title', 'description')
    # <--- POPRAWKA: Usunięto 'tags' z filter_horizontal
    filter_horizontal = ('categories',)
    
    # Pytania będą widoczne na stronie edycji testu, ale w uproszczonej formie
    # inlines = [QuestionInline] # Można odkomentować, jeśli chcemy widzieć pytania w teście

    fieldsets = (
        (None, {
            'fields': ('title', 'description')
        }),
        ('Organizacja', {
            # <--- POPRAWKA: Usunięto 'tags' z tego fieldsetu
            'fields': ('categories',)
        }),
    )

    @admin.display(description='Kategorie')
    def get_categories(self, obj):
        """Zwraca nazwy kategorii jako string, ładnie sformatowane."""
        return ", ".join([c.name for c in obj.categories.all()])


@admin.register(ReportedIssue)
class ReportedIssueAdmin(admin.ModelAdmin):
    """Konfiguracja panelu admina dla modelu ReportedIssue."""
    list_display = ('question', 'issue_type', 'status', 'created_at')
    list_filter = ('status', 'issue_type')
    search_fields = ('question__text', 'description')
    
    # Pola, które zawsze są tylko do odczytu
    readonly_fields = ('question', 'test', 'issue_type', 'description', 'ai_feedback_snapshot', 'created_at')

    fieldsets = (
        ('Informacje o Zgłoszeniu', {
            'fields': ('question', 'test', 'issue_type', 'created_at')
        }),
        ('Treść Zgłoszenia', {
            'fields': ('description', 'ai_feedback_snapshot')
        }),
        ('Zarządzanie Zgłoszeniem', {
            'fields': ('status',)
        }),
    )
