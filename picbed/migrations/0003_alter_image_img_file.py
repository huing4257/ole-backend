# Generated by Django 4.1.3 on 2023-04-04 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('picbed', '0002_remove_image_img_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='img_file',
            field=models.ImageField(upload_to='picbed/uploads/%Y/%m/%d/'),
        ),
    ]