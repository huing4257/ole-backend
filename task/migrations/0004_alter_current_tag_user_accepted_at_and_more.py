# Generated by Django 4.1.3 on 2023-04-08 09:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_alter_user_account_balance_alter_user_credit_score_and_more'),
        ('task', '0003_question_q_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='current_tag_user',
            name='accepted_at',
            field=models.FloatField(null=True),
        ),
        migrations.RemoveField(
            model_name='current_tag_user',
            name='tag_user',
        ),
        migrations.RemoveField(
            model_name='progress',
            name='tag_user',
        ),
        migrations.AlterField(
            model_name='question',
            name='result',
            field=models.ManyToManyField(default=[], to='task.result'),
        ),
        migrations.AlterField(
            model_name='result',
            name='tag_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.user'),
        ),
        migrations.AlterField(
            model_name='task',
            name='current_tag_user_list',
            field=models.ManyToManyField(default=[], to='task.current_tag_user'),
        ),
        migrations.AlterField(
            model_name='task',
            name='past_tag_user_list',
            field=models.ManyToManyField(default=[], to='user.user'),
        ),
        migrations.AlterField(
            model_name='task',
            name='progress',
            field=models.ManyToManyField(default=[], to='task.progress'),
        ),
        migrations.AlterField(
            model_name='task',
            name='questions',
            field=models.ManyToManyField(default=[], to='task.question'),
        ),
        migrations.AddField(
            model_name='current_tag_user',
            name='tag_user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='user.user'),
        ),
        migrations.AddField(
            model_name='progress',
            name='tag_user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='user.user'),
        ),
    ]
