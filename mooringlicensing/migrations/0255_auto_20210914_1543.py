# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-09-14 07:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mooringlicensing', '0254_remove_proposal_vessel_overall_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalsettings',
            name='key',
            field=models.CharField(choices=[('dcv_permit_template_file', 'DcvPermit template file'), ('dcv_admission_template_file', 'DcvAdmission template file'), ('approval_template_file', 'Approval template file'), ('wla_template_file', 'Waiting List Allocation template file'), ('aap_template_file', 'Annual Admission Permit template file'), ('aup_template_file', 'Authorised User Permit tempalte file'), ('ml_template_file', 'Mooring Licence template file'), ('minimum_vessel_length', 'Minimum vessel length'), ('minimum_mooring_vessel_length', 'Minimum mooring vessel length'), ('min_sticker_number_for_dcv_permit', 'Minimun sticker number for DCV Permit')], max_length=255),
        ),
    ]