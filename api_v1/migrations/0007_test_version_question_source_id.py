from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0006_question_type_cascade_grading'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='source_id',
            field=models.PositiveIntegerField(blank=True, help_text='File-local integer id from quiz JSON.', null=True),
        ),
        migrations.AddField(
            model_name='test',
            name='version',
            field=models.CharField(default='1.0', help_text='Quiz document version.', max_length=32),
        ),
        migrations.AddConstraint(
            model_name='question',
            constraint=models.UniqueConstraint(fields=('test', 'source_id'), name='unique_source_id_in_test'),
        ),
    ]
