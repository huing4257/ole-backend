# Generated by Django 4.1.3 on 2023-04-24 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_category_usercategory_delete_banuser_user_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='category',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
