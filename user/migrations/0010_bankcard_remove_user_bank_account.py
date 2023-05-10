# Generated by Django 4.1.3 on 2023-05-10 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_user_tag_score'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_id', models.CharField(max_length=255)),
                ('card_balance', models.IntegerField(default=0)),
            ],
        ),
        migrations.RemoveField(
            model_name='user',
            name='bank_account',
        ),
    ]