# Generated by Django 5.0.9 on 2024-09-25 02:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mooringlicensing', '0359_alter_proposalsitelicenseemooringrequest_mooring'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compliance',
            name='reminder_sent',
        ),
        migrations.AddField(
            model_name='compliance',
            name='due_reminder_count',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Number of times a due reminder has been sent'),
        ),
    ]