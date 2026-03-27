from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0003_add_default_prompt'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('total_questions', models.PositiveIntegerField(default=0)),
                ('correct_count', models.PositiveIntegerField(default=0)),
                ('score_achieved', models.FloatField(default=0)),
                ('score_possible', models.FloatField(default=0)),
                ('is_study_mode', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-started_at'],
                'indexes': [models.Index(fields=['user', 'started_at'], name='quizsession_user_started_idx')],
            },
        ),
        migrations.CreateModel(
            name='QuestionAttempt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_correct', models.BooleanField()),
                ('points_awarded', models.FloatField(default=0)),
                ('time_spent_secs', models.PositiveIntegerField(default=0)),
                ('answered_at', models.DateTimeField(auto_now_add=True)),
                ('difficulty_rating', models.CharField(blank=True, choices=[('easy', 'Easy'), ('normal', 'Normal'), ('hard', 'Hard')], max_length=10, null=True)),
                ('sr_interval', models.PositiveIntegerField(default=1)),
                ('sr_ease_factor', models.FloatField(default=2.5)),
                ('sr_next_review', models.DateField(blank=True, null=True)),
                ('sr_repetitions', models.PositiveIntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_attempts', to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='api_v1.question')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='api_v1.test')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='api_v1.quizsession')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['user', 'question'], name='attempt_user_question_idx'),
                    models.Index(fields=['user', 'sr_next_review'], name='attempt_user_sr_next_idx'),
                    models.Index(fields=['session'], name='attempt_session_idx'),
                    models.Index(fields=['answered_at'], name='attempt_answered_at_idx'),
                ],
            },
        ),
    ]
