# Generated by Django 2.1.5 on 2019-02-02 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0006_auto_20190201_1247'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='post_privacy',
            field=models.CharField(default='public', max_length=50, null=True),
        ),
    ]
