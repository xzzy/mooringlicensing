from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from mooringlicensing.components.compliances.models import Compliance
from ledger_api_client.models import EmailUser

import logging

from mooringlicensing.management.commands.utils import construct_email_message

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')


class Command(BaseCommand):
    help = 'Send notification emails for compliances which has past due dates, and also reminder notification emails for those that are within the daterange prior to due_date (eg. within 14 days of due date)'

    def handle(self, *args, **options):

        errors = []
        updates = []
        today = timezone.localtime(timezone.now()).date()
        logger.info('Running command {}'.format(__name__))

        for c in Compliance.objects.filter(processing_status=Compliance.PROCESSING_STATUS_DUE):
            try:
                c.send_reminder()
                c.save()
                updates.append(c.lodgement_number)
            except Exception as e:
                err_msg = 'Error sending Reminder Compliance'.format(c.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        # err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(errors)>0 else '<strong style="color: green;">Errors: 0</strong>'
        # msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)
