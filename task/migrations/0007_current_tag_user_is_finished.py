# Generated by Django 4.1.3 on 2023-04-16 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0006_task_tag_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='current_tag_user',
            name='is_finished',
            field=models.BooleanField(default=False),
        ),
    ]
