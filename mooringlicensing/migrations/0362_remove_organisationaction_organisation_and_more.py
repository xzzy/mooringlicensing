# Generated by Django 5.0.9 on 2024-10-09 02:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mooringlicensing', '0361_alter_globalsettings_key'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organisationaction',
            name='organisation',
        ),
        migrations.RemoveField(
            model_name='proposal',
            name='org_applicant',
        ),
        migrations.RemoveField(
            model_name='approval',
            name='org_applicant',
        ),
        migrations.RemoveField(
            model_name='organisationlogentry',
            name='organisation',
        ),
        migrations.DeleteModel(
            name='OrganisationAccessGroup',
        ),
        migrations.AlterUniqueTogether(
            name='organisationcontact',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='organisationlogdocument',
            name='log_entry',
        ),
        migrations.RemoveField(
            model_name='organisationlogentry',
            name='communicationslogentry_ptr',
        ),
        migrations.RemoveField(
            model_name='organisationrequestuseraction',
            name='request',
        ),
        migrations.RemoveField(
            model_name='organisationrequestlogentry',
            name='request',
        ),
        migrations.RemoveField(
            model_name='organisationrequestdeclineddetails',
            name='request',
        ),
        migrations.RemoveField(
            model_name='organisationrequestlogdocument',
            name='log_entry',
        ),
        migrations.RemoveField(
            model_name='organisationrequestlogentry',
            name='communicationslogentry_ptr',
        ),
        migrations.AlterUniqueTogether(
            name='userdelegation',
            unique_together=None,
        ),
        migrations.DeleteModel(
            name='OrganisationAction',
        ),
        migrations.DeleteModel(
            name='OrganisationContact',
        ),
        migrations.DeleteModel(
            name='Organisation',
        ),
        migrations.DeleteModel(
            name='UserDelegation',
        ),
        migrations.DeleteModel(
            name='OrganisationLogDocument',
        ),
        migrations.DeleteModel(
            name='OrganisationLogEntry',
        ),
        migrations.DeleteModel(
            name='OrganisationRequestUserAction',
        ),
        migrations.DeleteModel(
            name='OrganisationRequest',
        ),
        migrations.DeleteModel(
            name='OrganisationRequestDeclinedDetails',
        ),
        migrations.DeleteModel(
            name='OrganisationRequestLogDocument',
        ),
        migrations.DeleteModel(
            name='OrganisationRequestLogEntry',
        ),
    ]