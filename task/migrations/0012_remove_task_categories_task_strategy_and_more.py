# Generated by Django 4.1.3 on 2023-04-24 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_alter_category_category'),
        ('task', '0011_alter_task_check_result'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='categories',
        ),
        migrations.AddField(
            model_name='task',
            name='strategy',
            field=models.CharField(default='order', max_length=255),
        ),
        migrations.RemoveField(
            model_name='task',
            name='task_style',
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.AddField(
            model_name='task',
            name='task_style',
            field=models.ManyToManyField(default=[], to='user.category'),
        ),
    ]
