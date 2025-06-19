from rest_framework import serializers

class QuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    questionText = serializers.CharField()
    image = serializers.CharField(allow_blank=True, required=False) # Ścieżka do obrazka
    type = serializers.ChoiceField(choices=['single-choice', 'multiple-choice', 'open-ended'])
    tags = serializers.ListField(child=serializers.CharField())
    options = serializers.ListField(child=serializers.CharField(), allow_blank=True, required=False))
    correctAnswers = serializers.ListField(child=serializers.IntegerField(), allow_blank=True, required=False)) # Indeksy poprawnych opcji
    explanation = serializers.CharField()
    gradingCriteria = serializers.CharField(allow_blank=True, required=False) # Kryteria oceniania
    maxPoints = serializers.IntegerField(default=1, required=False) # Maksymalna liczba punktów za pytanie

class TestMetadataSerializer(serializers.Serializer):
    category = serializers.CharField()
    scope = serializers.CharField()
    version = serializers.CharField()
    test_id = serializers.CharField() # Np. nazwa pliku JSON bez rozszerzenia
    question_count = serializers.IntegerField()