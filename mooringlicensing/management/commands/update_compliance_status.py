from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from mooringlicensing.components.compliances.models import Compliance, ComplianceUserAction
from mooringlicensing.components.main.models import NumberOfDaysSetting, NumberOfDaysType
import datetime

import logging

from mooringlicensing.management.commands.utils import construct_email_message
from mooringlicensing.settings import CODE_DAYS_BEFORE_DUE_COMPLIANCE

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')


class Command(BaseCommand):
    help = 'Change the status of Compliances from future to due when they are close to due date'

    def handle(self, *args, **options):
        today = timezone.localtime(timezone.now()).date()
        days_type = NumberOfDaysType.objects.get(code=CODE_DAYS_BEFORE_DUE_COMPLIANCE)
        days_setting = NumberOfDaysSetting.get_setting_by_date(days_type, today)
        compare_date = today + datetime.timedelta(days=days_setting.number_of_days)

        errors = []
        updates = []
        logger.info('Running command {}'.format(__name__))

        # Future --> Due
        queries = Q()
        queries &= Q(due_date__gte=today)
        queries &= Q(due_date__lte=compare_date)
        queries &= Q(lodgement_date__isnull=True)
        queries &= Q(processing_status__in=[Compliance.PROCESSING_STATUS_FUTURE,])
        compliances_to_be_due = Compliance.objects.filter(queries)
        for c in compliances_to_be_due:
            try:
                c.processing_status = Compliance.PROCESSING_STATUS_DUE
                c.customer_status = Compliance.CUSTOMER_STATUS_DUE
                c.save()
                ComplianceUserAction.log_action(c, ComplianceUserAction.ACTION_STATUS_CHANGE.format(c.id))
                logger.info('updated Compliance {} status to {}'.format(c.id, c.processing_status))
                updates.append(c.lodgement_number)
            except Exception as e:
                err_msg = 'Error updating Compliance {} status'.format(c.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)

        # Future/Due --> Overdue
        queries = Q()
        queries &= Q(due_date__lt=today)
        queries &= Q(lodgement_date__isnull=True)
        queries &= Q(processing_status__in=[Compliance.PROCESSING_STATUS_DUE, Compliance.PROCESSING_STATUS_FUTURE,])
        compliances_to_be_overdue = Compliance.objects.filter(queries)
        for c in compliances_to_be_overdue:
            try:
                c.processing_status = Compliance.PROCESSING_STATUS_OVERDUE
                c.customer_status = Compliance.CUSTOMER_STATUS_OVERDUE
                c.save()
                ComplianceUserAction.log_action(c, ComplianceUserAction.ACTION_STATUS_CHANGE.format(c.id), None)
                logger.info('updated Compliance {} status to {}'.format(c.id, c.processing_status))
                updates.append(c.lodgement_number)
            except Exception as e:
                err_msg = 'Error updating Compliance {} status'.format(c.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)
