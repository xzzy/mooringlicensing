# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-06-01 06:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mooringlicensing', '0129_auto_20210531_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='approval',
            name='wla_queue_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]