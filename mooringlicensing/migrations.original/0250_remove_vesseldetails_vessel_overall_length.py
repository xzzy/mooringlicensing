# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-09-13 02:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mooringlicensing', '0249_auto_20210913_0945'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vesseldetails',
            name='vessel_overall_length',
        ),
    ]