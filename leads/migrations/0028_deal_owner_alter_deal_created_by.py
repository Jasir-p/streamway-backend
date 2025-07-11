# Generated by Django 5.1.8 on 2025-06-17 04:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0027_alter_deal_account_id'),
        ('users', '0012_alter_employee_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deals_owned', to='users.employee'),
        ),
        migrations.AlterField(
            model_name='deal',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deals_created', to='users.employee'),
        ),
    ]
