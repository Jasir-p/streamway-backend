# Generated by Django 5.1.4 on 2025-03-12 05:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='leadformfield',
            name='options',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
