# Generated by Django 4.1.3 on 2023-04-16 17:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0002_anslist_delete_anslistdata'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='anslist',
            name='task',
        ),
    ]
