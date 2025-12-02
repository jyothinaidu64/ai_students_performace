from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assessments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="assessment",
            name="topic",
            field=models.CharField(
                max_length=200,
                null=True,
                blank=True,
                help_text="Chapter / topic name (e.g. 'Quadratic Equations', 'Life Processes')",
            ),
        ),
    ]
