# Generated by Django 5.1.4 on 2025-03-27 07:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0007_alter_leadacess_lead'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='leadacess',
            name='lead',
        ),
        migrations.AddField(
            model_name='leadacess',
            name='lead',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='leads.leads'),
        ),
    ]
