# Generated by Django 5.1.8 on 2025-06-02 05:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0010_remove_accounts_notes_notes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='lead',
        ),
        migrations.AddField(
            model_name='contact',
            name='account_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Customer.accounts'),
        ),
    ]
