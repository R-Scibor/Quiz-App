from rest_framework import serializers
from .models import Test, Question, Answer, Category, Tag, ReportedIssue
from django.db.models import Count, Q

# -----------------------------------------------------------------------------
# Wprowadzenie do Serializerów
# -----------------------------------------------------------------------------
#
# Serializery w Django REST Framework działają jak "tłumacze". Konwertują
# złożone typy danych, takie jak obiekty modeli Django, na natywne typy
# Pythona, które następnie można łatwo renderować jako JSON, XML itp.
#
# Poniższe serializery zostały przepisane, aby korzystać z potęgi
# `ModelSerializer`. Automatycznie generują pola na podstawie modeli,
# co redukuje ilość powtarzalnego kodu i ułatwia utrzymanie.
#
# Kluczowe techniki użyte poniżej:
#
# 1.  **ModelSerializer**: Podstawa naszych nowych serializerów.
#
# 2.  **Zagnieżdżone Serializery**: Aby w jednym obiekcie JSON (np. Pytanie)
#     znalazły się dane z powiązanych modeli (np. Tagi, Odpowiedzi).
#
# 3.  **SlugRelatedField**: Użyty do reprezentowania tagów jako prostej
#     listy stringów (ich nazw), co jest zgodne z oczekiwaniami frontendu.
#
# 4.  **SerializerMethodField**: Użyte do generowania pól, których wartości
#     muszą być obliczone dynamicznie (np. `options` i `correctAnswers`
#     w pytaniu lub `question_counts` w teście). To pozwala nam idealnie
#     odwzorować starą strukturę JSON.
#
# 5.  **source**: Atrybut używany do mapowania pól modelu na inne nazwy
#     w JSON (np. pole `text` w modelu -> `questionText` w JSON).
#
# -----------------------------------------------------------------------------

class TagSerializer(serializers.ModelSerializer):
    """Prosty serializer dla modelu Tag."""
    class Meta:
        model = Tag
        fields = ['name']

class AnswerSerializer(serializers.ModelSerializer):
    """
    Serializer dla modelu Answer. Zwraca tylko treść i informację,
    czy odpowiedź jest poprawna.
    """
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer dla modelu Question.
    Zaprojektowany tak, aby struktura wyjściowego JSON była w 100%
    zgodna z formatem, którego oczekuje frontend.
    """
    # Mapowanie pól modelu na nazwy z oryginalnego JSON-a
    questionText = serializers.CharField(source='text')
    type = serializers.CharField(source='question_type')
    gradingCriteria = serializers.CharField(source='grading_criteria')
    maxPoints = serializers.IntegerField(source='max_points')
    image = serializers.URLField()
    
    # Zagnieżdżony serializer dla tagów, zwracający listę ich nazw
    tags = serializers.StringRelatedField(many=True)

    # Pola generowane dynamicznie w celu dopasowania do starej struktury
    options = serializers.SerializerMethodField()
    correctAnswers = serializers.SerializerMethodField()

    
    class Meta:
        model = Question
        # Lista pól, które mają zostać zwrócone w JSON
        fields = [
            'id', 'questionText', 'image', 'type', 'tags', 'options', 
            'correctAnswers', 'explanation', 'gradingCriteria', 'maxPoints'
        ]
    def get_options(self, obj):
        """
        Zbiera teksty wszystkich odpowiedzi powiązanych z tym pytaniem
        i zwraca je jako listę stringów.
        """
        # `obj.answers` jest możliwe dzięki `prefetch_related` w widoku
        return [answer.text for answer in obj.answers.all()]

    def get_correctAnswers(self, obj):
        """
        Znajduje indeksy poprawnych odpowiedzi i zwraca je jako listę.
        """
        correct_indices = []
        # `obj.answers` jest możliwe dzięki `prefetch_related` w widoku
        for i, answer in enumerate(obj.answers.all()):
            if answer.is_correct:
                correct_indices.append(i)
        return correct_indices


class QuestionCountSerializer(serializers.Serializer):
    """
    Wewnętrzny serializator dla zagnieżdżonych liczników pytań.
    Nie jest to ModelSerializer, ponieważ nie ma bezpośredniego modelu.
    """
    closed = serializers.IntegerField()
    open = serializers.IntegerField()
    total = serializers.IntegerField()


class TestMetadataSerializer(serializers.ModelSerializer):
    """
    Serializer dla metadanych Testu.
    Pobiera dane z modelu Test i agreguje liczniki pytań.
    """
    # Mapowanie pól i relacji na nazwy z oryginalnego JSON-a
    category = serializers.CharField(source='categories.first.name', default=None)
    scope = serializers.CharField(source='title')
    version = serializers.SerializerMethodField()
    test_id = serializers.UUIDField(source='id')
    question_counts = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = ['category', 'scope', 'version', 'test_id', 'question_counts']

    def get_version(self, obj):
        """Zwraca statyczną wersję. Można to rozbudować w przyszłości."""
        return "2.0-db"

    def get_question_counts(self, obj):
        """

        Dynamicznie oblicza liczbę pytań otwartych, zamkniętych i wszystkich
        dla danego testu. `obj.questions` jest wydajne dzięki `prefetch_related` w widoku.
        """
        
        # Sprawdzamy, czy dane zostały załadowane z adnotacją
        if hasattr(obj, 'open_questions_count'):
            counts = {
                'open': obj.open_questions_count,
                'closed': obj.closed_questions_count,
                'total': obj.total_questions_count,
            }
        else: # Fallback, jeśli adnotacje nie są dostępne (mniej wydajne)
             all_questions = obj.questions.all()
             counts = {
                 'open': all_questions.filter(question_type=Question.OPEN_ENDED).count(),
                 'closed': all_questions.filter(question_type__in=[Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE]).count(),
                 'total': all_questions.count()
             }

        serializer = QuestionCountSerializer(data=counts)
        serializer.is_valid(raise_exception=True)
        return serializer.data


class ReportedIssueSerializer(serializers.ModelSerializer):
    """
    Serializer do tworzenia nowych zgłoszeń problemów.
    Waliduje dane przychodzące z frontendu.
    """
    # Dodajemy jawne definicje pól, aby zapewnić prawidłową obsługę kluczy obcych (UUID)
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    test = serializers.PrimaryKeyRelatedField(queryset=Test.objects.all())

    class Meta:
        model = ReportedIssue
        fields = [
            'question',
            'test',
            'issue_type',
            'description',
            'ai_feedback_snapshot'
        ]

    def validate(self, attrs):
        """
        Dodatkowa walidacja logiki biznesowej.
        """
        question = attrs.get('question')
        test = attrs.get('test')

        # Sprawdzamy, czy pytanie faktycznie należy do podanego testu.
        if question and test and question.test != test:
            raise serializers.ValidationError({"detail": "To pytanie nie należy do podanego testu."})

        # Jeśli typem zgłoszenia jest błąd oceny AI, pole ai_feedback_snapshot jest wymagane.
        if attrs.get('issue_type') == 'AI_GRADING_ERROR' and not attrs.get('ai_feedback_snapshot'):
            raise serializers.ValidationError({
                'ai_feedback_snapshot': 'Zapis odpowiedzi AI jest wymagany przy zgłaszaniu błędu oceny.'
            })
            
        return attrs
