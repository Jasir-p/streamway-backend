# Generated by Django 5.1.8 on 2025-06-02 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0012_alter_contact_account_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='department',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
