# Generated by Django 5.1.4 on 2025-02-19 14:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Main_rbac', '0002_remove_permission_tenant'),
        ('rabc', '0008_tenantpermission'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoleAcessPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permission', to='Main_rbac.permission')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role', to='rabc.role')),
            ],
        ),
    ]
