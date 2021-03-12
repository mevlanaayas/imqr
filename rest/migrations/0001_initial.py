# Generated by Django 3.1.7 on 2021-03-11 23:34

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='QR',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.UUIDField()),
                ('qr', models.UUIDField()),
                ('content_type', models.CharField(max_length=4)),
            ],
        ),
    ]
