# Generated by Django 5.1.8 on 2025-05-14 02:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0003_alter_message_read_by'),
        ('users', '0012_alter_employee_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='read_by',
            field=models.ManyToManyField(blank=True, related_name='read_messages', to='users.employee'),
        ),
    ]
