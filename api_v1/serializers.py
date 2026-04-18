from rest_framework import serializers
from .models import Test, Question, Answer, Category, Tag, ReportedIssue, QuizSession, QuestionAttempt
from django.db.models import Count, Q
from django.contrib.auth.models import User

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    questionText = serializers.CharField(source='text')
    type = serializers.CharField(source='question_type')
    gradingCriteria = serializers.CharField(source='grading_criteria')
    maxPoints = serializers.IntegerField(source='max_points')
    image = serializers.URLField()
    test_id = serializers.UUIDField(source='test.id')
    tags = serializers.StringRelatedField(many=True)
    options = serializers.SerializerMethodField()
    correctAnswers = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id', 'test_id', 'questionText', 'image', 'type', 'tags', 'options',
            'correctAnswers', 'explanation', 'gradingCriteria', 'maxPoints'
        ]

    def get_options(self, obj):
        return [answer.text for answer in obj.answers.all()]

    def get_correctAnswers(self, obj):
        return [i for i, answer in enumerate(obj.answers.all()) if answer.is_correct]


class QuestionCountSerializer(serializers.Serializer):
    closed = serializers.IntegerField()
    open = serializers.IntegerField()
    total = serializers.IntegerField()


class TestMetadataSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='categories.first.name', default=None)
    scope = serializers.CharField(source='title')
    version = serializers.SerializerMethodField()
    test_id = serializers.UUIDField(source='id')
    question_counts = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = ['category', 'scope', 'version', 'test_id', 'question_counts']

    def get_version(self, obj):
        return "2.0-db"

    def get_question_counts(self, obj):
        if hasattr(obj, 'open_questions_count'):
            counts = {
                'open': obj.open_questions_count,
                'closed': obj.closed_questions_count,
                'total': obj.total_questions_count,
            }
        else:  # fallback when annotations are unavailable
             all_questions = obj.questions.all()
             counts = {
                 'open': all_questions.filter(question_type__in=[Question.OPEN_TEXT, Question.OPEN_CLI, Question.OPEN_CODE]).count(),
                 'closed': all_questions.filter(question_type__in=[Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE]).count(),
                 'total': all_questions.count()
             }

        serializer = QuestionCountSerializer(data=counts)
        serializer.is_valid(raise_exception=True)
        return serializer.data


class ReportedIssueSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    test = serializers.PrimaryKeyRelatedField(queryset=Test.objects.all())
    user_answer_choices = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = ReportedIssue
        fields = [
            'question',
            'test',
            'issue_type',
            'description',
            'ai_feedback_snapshot',
            'user_answer_open',
            'user_answer_choices'
        ]

    def validate(self, attrs):
        question = attrs.get('question')
        test = attrs.get('test')
        user_answer_open = attrs.get('user_answer_open')
        user_answer_choices = attrs.get('user_answer_choices')

        # Sprawdzamy, czy pytanie faktycznie należy do podanego testu.
        if question and test and question.test != test:
            raise serializers.ValidationError({"detail": "This question does not belong to the given test."})

        if attrs.get('issue_type') == 'AI_GRADING_ERROR' and not attrs.get('ai_feedback_snapshot'):
            raise serializers.ValidationError({
                'ai_feedback_snapshot': 'A snapshot of the AI response is required when reporting a grading error.'
            })

        if question:
            if question.question_type in [Question.OPEN_TEXT, Question.OPEN_CLI, Question.OPEN_CODE]:
                if not user_answer_open:
                    raise serializers.ValidationError({'user_answer_open': 'User answer is required for open questions.'})
                if user_answer_choices:
                    raise serializers.ValidationError({'user_answer_choices': 'Choice answers are not allowed for open questions.'})

            elif question.question_type in [Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE]:
                if not user_answer_choices:
                    raise serializers.ValidationError({'user_answer_choices': 'User answer is required for closed questions.'})
                if user_answer_open:
                    raise serializers.ValidationError({'user_answer_open': 'Text answers are not allowed for closed questions.'})

        return attrs

    def create(self, validated_data):
        return ReportedIssue.objects.create(**validated_data)


class QuizSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSession
        fields = ['id', 'started_at', 'completed_at', 'total_questions', 'correct_count',
                  'score_achieved', 'score_possible', 'is_study_mode']
        read_only_fields = ['id', 'started_at']


class QuestionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAttempt
        fields = ['question', 'test', 'session', 'is_correct', 'points_awarded',
                  'time_spent_secs', 'difficulty_rating']


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
        )
