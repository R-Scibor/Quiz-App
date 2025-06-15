from rest_framework import serializers

class QuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    questionText = serializers.CharField()
    image = serializers.CharField(allow_blank=True, required=False) # Ścieżka do obrazka
    type = serializers.ChoiceField(choices=['single-choice', 'multiple-choice'])
    tags = serializers.ListField(child=serializers.CharField())
    options = serializers.ListField(child=serializers.CharField())
    correctAnswers = serializers.ListField(child=serializers.IntegerField()) # Indeksy poprawnych opcji
    explanation = serializers.CharField()

class TestMetadataSerializer(serializers.Serializer):
    category = serializers.CharField()
    scope = serializers.CharField()
    version = serializers.CharField()
    test_id = serializers.CharField() # Np. nazwa pliku JSON bez rozszerzenia
    question_count = serializers.IntegerField()