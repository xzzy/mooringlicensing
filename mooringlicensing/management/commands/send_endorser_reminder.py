from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mooringlicensing.components.compliances.models import Compliance
from ledger.accounts.models import EmailUser

import logging

from mooringlicensing.components.main.models import NumberOfDaysType, NumberOfDaysSetting
from mooringlicensing.settings import CODE_DAYS_FOR_ENDORSER_AUA

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send email to authorised user application endorser if application is not endorsed or declined within configurable number of days'

    def handle(self, *args, **options):
        try:
            user = EmailUser.objects.get(email=settings.CRON_EMAIL)
        except:
            user = EmailUser.objects.create(email=settings.CRON_EMAIL, password='')

        errors = []
        updates = []
        today = timezone.localtime(timezone.now()).date()

        # Retrieve the number of days before expiry date of the approvals to email
        days_type = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_ENDORSER_AUA)
        days_setting = NumberOfDaysSetting.get_setting_by_date(days_type, today)
        if not days_setting:
            # No number of days found
            raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type.name, today))

        logger.info('Running command {}'.format(__name__))
        for c in Compliance.objects.filter(processing_status=Compliance.PROCESSING_STATUS_DUE):
            try:
                c.send_reminder(user)
                c.save()
                updates.append(c.lodgement_number)
            except Exception as e:
                err_msg = 'Error sending Reminder Compliance'.format(c.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(errors) > 0 else '<strong style="color: green;">Errors: 0</strong>'
        msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        logger.info(msg)
        print(msg)  # will redirect to cron_tasks.log file, by the parent script
