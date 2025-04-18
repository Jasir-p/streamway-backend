# Generated by Django 5.1.4 on 2025-02-26 14:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_team_teammembers'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='members',
            field=models.ManyToManyField(related_name='team_memberships', through='users.TeamMembers', to='users.employee'),
        ),
        migrations.AlterField(
            model_name='teammembers',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_members', to='users.team'),
        ),
    ]
