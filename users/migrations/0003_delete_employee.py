# Generated by Django 5.1.4 on 2025-02-22 15:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_employee_last_login'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Employee',
        ),
    ]
