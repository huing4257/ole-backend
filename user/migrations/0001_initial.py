# Generated by Django 4.1.3 on 2023-04-03 15:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('user_id', models.AutoField(primary_key=True, serialize=False)),
                ('user_name', models.CharField(max_length=200, unique=True)),
                ('password', models.BinaryField()),
                ('user_type', models.CharField(max_length=20)),
                ('score', models.IntegerField(default=0)),
                ('membership_level', models.IntegerField(default=0)),
                ('invite_code', models.CharField(max_length=20)),
                ('credit_score', models.IntegerField(default=0)),
                ('bank_account', models.CharField(default='', max_length=20)),
                ('account_balance', models.IntegerField(default=0)),
                ('grow_value', models.IntegerField(default=0)),
                ('vip_expire_time', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='UserToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=100, unique=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.user')),
            ],
            options={
                'db_table': 'user_token',
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['user_name'], name='user_user_user_na_62bc91_idx'),
        ),
    ]
