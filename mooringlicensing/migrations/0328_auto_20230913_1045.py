# Generated by Django 3.2.20 on 2023-09-13 02:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mooringlicensing', '0327_remove_vesselownership_company_ownership'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vesselownership',
            name='company_ownerships',
        ),
        migrations.CreateModel(
            name='VesselOwnershipCompanyOwnership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('approved', 'Approved'), ('draft', 'Draft'), ('old', 'Old'), ('declined', 'Declined')], default='draft', max_length=50)),
                ('company_ownership', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mooringlicensing.companyownership')),
                ('vessel_ownership', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mooringlicensing.vesselownership')),
            ],
        ),
        migrations.AddField(
            model_name='vesselownership',
            name='company_ownerships2',
            field=models.ManyToManyField(blank=True, null=True, related_name='vessel_ownerships', through='mooringlicensing.VesselOwnershipCompanyOwnership', to='mooringlicensing.CompanyOwnership'),
        ),
    ]