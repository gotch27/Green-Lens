# Generated for the GreenLens backend MVP API contract.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scans", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name="scan",
            old_name="location",
            new_name="city",
        ),
        migrations.AlterField(
            model_name="scan",
            name="city",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="scan",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="scans",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="scan",
            name="temperature",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="scan",
            name="humidity",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="scan",
            name="weather_recommendation",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="result",
            name="is_sick",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="result",
            name="diagnosis",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="result",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="result",
            name="characteristics",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="result",
            name="treatment_steps",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="result",
            name="links",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="result",
            name="confidence",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.RemoveField(
            model_name="result",
            name="recommendation",
        ),
    ]
