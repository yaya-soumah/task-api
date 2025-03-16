# Generated by Django 5.1.7 on 2025-03-15 04:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_urgenttask_dependencies'),
    ]

    operations = [
        migrations.AddField(
            model_name='urgenttask',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='tasks.urgenttask'),
        ),
    ]
