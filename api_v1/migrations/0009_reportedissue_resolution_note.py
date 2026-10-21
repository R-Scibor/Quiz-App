from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0008_question_retired'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportedissue',
            name='resolution_note',
            field=models.TextField(
                blank=True,
                help_text='Staff note recorded when the report is triaged.',
                null=True,
            ),
        ),
    ]
