# Generated by Django 5.1.8 on 2025-04-18 05:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0006_accounts_address_accounts_notes_accounts_status'),
        ('activities', '0001_initial'),
        ('leads', '0020_alter_leads_form_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='task',
            name='object_id',
        ),
        migrations.AddField(
            model_name='task',
            name='account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='Customer.accounts'),
        ),
        migrations.AddField(
            model_name='task',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='Customer.contact'),
        ),
        migrations.AddField(
            model_name='task',
            name='lead',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='leads.leads'),
        ),
    ]
