from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0007_test_version_question_source_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='retired',
            field=models.BooleanField(
                default=False,
                help_text='Hidden from new quiz sessions and the study queue. Attempt history is kept.',
            ),
        ),
    ]
