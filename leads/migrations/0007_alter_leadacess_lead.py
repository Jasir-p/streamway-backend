# Generated by Django 5.1.4 on 2025-03-27 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0006_remove_leadacess_lead_leadacess_lead'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leadacess',
            name='lead',
            field=models.ManyToManyField(related_name='accesses', to='leads.leads'),
        ),
    ]
