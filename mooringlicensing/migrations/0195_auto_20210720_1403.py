# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-07-20 06:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mooringlicensing', '0194_merge_20210719_1028'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sticker',
            name='vessel',
        ),
        migrations.AddField(
            model_name='sticker',
            name='vessel_ownership',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mooringlicensing.VesselOwnership'),
        ),
        migrations.AlterField(
            model_name='approval',
            name='status',
            field=models.CharField(choices=[('current', 'Current'), ('expired', 'Expired'), ('cancelled', 'Cancelled'), ('surrendered', 'Surrendered'), ('suspended', 'Suspended'), ('extended', 'Extended'), ('awaiting_payment', 'Awaiting Payment')], default='current', max_length=40),
        ),
    ]