# Generated by Django 4.1.3 on 2023-04-16 15:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('task', '0008_current_tag_user_is_check_accepted'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnsData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('std_ans', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='AnsListData',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('ans_list', models.ManyToManyField(default=[], to='review.ansdata')),
                ('task', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='task.task')),
            ],
        ),
    ]
