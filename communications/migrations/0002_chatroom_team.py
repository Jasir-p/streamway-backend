# Generated by Django 5.1.8 on 2025-05-13 05:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0001_initial'),
        ('users', '0012_alter_employee_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.team'),
        ),
    ]
