from datetime import timedelta

from django.utils import timezone
from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q

import logging

from mooringlicensing.components.proposals.email import send_payment_reminder_email
from mooringlicensing.components.main.models import NumberOfDaysType, NumberOfDaysSetting
from mooringlicensing.components.proposals.models import Proposal
from mooringlicensing.management.commands.utils import construct_email_message
from mooringlicensing.settings import CODE_DAYS_FOR_DUE_PAYMENT_REMINDER

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')

class Command(BaseCommand):
    help = 'send email reminder to applicant to submit payment for an application if not paid within configurable number of days after being approved'

    def handle(self, *args, **options):
        errors = []
        updates = []
        today = timezone.localtime(timezone.now()).date()

        # Retrieve the number of days before expiry date of the proposals to email
        days_type = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_DUE_PAYMENT_REMINDER)
        days_setting = NumberOfDaysSetting.get_setting_by_date(days_type, today)
        if not days_setting:
            # No number of days found
            raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type.name, today))
        boundary_date = today - timedelta(days=days_setting.number_of_days)

        logger.info('Running command {}'.format(__name__))

        # Construct queries
        queries = Q()
        queries &= Q(processing_status__in=(Proposal.PROCESSING_STATUS_AWAITING_PAYMENT))
        queries &= Q(payment_due_date__lt=boundary_date)
        queries &= Q(payment_reminder_sent=False)

        for p in Proposal.objects.filter(queries):
            try:
                p.payment_reminder_sent = True
                p.save()
                send_payment_reminder_email(p)
                logger.info('Payment reminder sent for Proposal {}'.format(p.lodgement_number))
                updates.append(p.lodgement_number)
            except Exception as e:
                err_msg = 'Error sending payment reminder for Proposal {}'.format(p.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)
