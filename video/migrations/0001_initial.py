# Generated by Django 4.1.3 on 2023-05-04 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('video_id', models.AutoField(primary_key=True, serialize=False)),
                ('video_file', models.FileField(upload_to='data/video/uploads/%Y/%m/%d/')),
                ('filename', models.CharField(max_length=255, null=True)),
            ],
        ),
    ]
