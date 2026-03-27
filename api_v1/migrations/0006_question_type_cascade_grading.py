from django.db import migrations, models


def rename_open_ended_to_open_text(apps, schema_editor):
    Question = apps.get_model('api_v1', 'Question')
    Question.objects.filter(question_type='open-ended').update(question_type='open-text')


def rename_open_text_to_open_ended(apps, schema_editor):
    Question = apps.get_model('api_v1', 'Question')
    Question.objects.filter(question_type='open-text').update(question_type='open-ended')


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0005_add_max_points_validators'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(
                choices=[
                    ('single-choice', 'Jednokrotnego wyboru'),
                    ('multiple-choice', 'Wielokrotnego wyboru'),
                    ('open-text', 'Otwarte (tekst)'),
                    ('open-cli', 'Otwarte (polecenie CLI)'),
                    ('open-code', 'Otwarte (kod)'),
                ],
                default='single-choice',
                help_text='Typ pytania (jednokrotnego wyboru, wielokrotnego wyboru, otwarte).',
                max_length=20,
            ),
        ),
        migrations.RunPython(rename_open_ended_to_open_text, rename_open_text_to_open_ended),
    ]
