# Generated by Django 4.1.3 on 2023-05-16 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0024_remove_reportinfo_user_reportinfo_report_req_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inputtype',
            name='tag_type',
            field=models.ManyToManyField(null=True, to='task.tagtype'),
        ),
    ]
