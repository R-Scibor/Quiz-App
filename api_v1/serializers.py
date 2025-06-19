from rest_framework import serializers

class QuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    questionText = serializers.CharField()
    image = serializers.CharField(allow_blank=True, required=False) # Ścieżka do obrazka
    type = serializers.ChoiceField(choices=['single-choice', 'multiple-choice', 'open-ended'])
    tags = serializers.ListField(child=serializers.CharField())
    options = serializers.ListField(child=serializers.CharField(), required=False)
    correctAnswers = serializers.ListField(child=serializers.IntegerField(), required=False) # Indeksy poprawnych opcji
    explanation = serializers.CharField()
    gradingCriteria = serializers.CharField(required=False)
    maxPoints = serializers.IntegerField(required=False)


class QuestionCountSerializer(serializers.Serializer):
    """Wewnętrzny serializator dla zagnieżdżonych liczników pytań."""
    closed = serializers.IntegerField()
    open = serializers.IntegerField()
    total = serializers.IntegerField()

class TestMetadataSerializer(serializers.Serializer):
    category = serializers.CharField()
    scope = serializers.CharField()
    version = serializers.CharField()
    test_id = serializers.CharField() # Np. nazwa pliku JSON bez rozszerzenia
    question_counts = QuestionCountSerializer()