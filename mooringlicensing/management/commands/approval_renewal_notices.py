from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mooringlicensing.components.approvals.models import Approval
from ledger.accounts.models import EmailUser
from datetime import timedelta
from mooringlicensing.components.approvals.email import ( send_approval_renewal_email_notification,)

import itertools

import logging

from mooringlicensing.components.main.models import NumberOfDaysType, NumberOfDaysSetting
from mooringlicensing.settings import CODE_DAYS_FOR_RENEWAL

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send Approval renewal notice when approval is due to expire in 30 days'

    def handle(self, *args, **options):
        try:
            user = EmailUser.objects.get(email=settings.CRON_EMAIL)
        except:
            user = EmailUser.objects.create(email=settings.CRON_EMAIL, password = '')

        errors = []
        updates = []

        today = timezone.localtime(timezone.now()).date()
        days_type = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_RENEWAL)
        days_setting = NumberOfDaysSetting.get_setting_by_date(days_type, today)
        if not days_setting:
            raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type.name, today))
        expiry_notification_date = today + timedelta(days=days_setting.number_of_days)
        renewal_conditions = {
            'expiry_date__lte': expiry_notification_date,
            'renewal_sent': False,
            'replaced_by__isnull': True
        }

        logger.info('Running command {}'.format(__name__))
        for a in Approval.objects.filter(**renewal_conditions):
            if a.status == Approval.STATUS_CURRENT or a.status == Approval.STATUS_SUSPENDED:
                try:
                    #import ipdb; ipdb.set_trace()
                    a.generate_renewal_doc()
                    send_approval_renewal_email_notification(a)
                    a.renewal_sent = True
                    a.save()
                    logger.info('Renewal notice sent for Approval {}'.format(a.id))
                    updates.append(a.lodgement_number)
                except Exception as e:
                    err_msg = 'Error sending renewal notice for Approval {}'.format(a.lodgement_number)
                    logger.error('{}\n{}'.format(err_msg, str(e)))
                    errors.append(err_msg)

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(errors)>0 else '<strong style="color: green;">Errors: 0</strong>'
        msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        logger.info(msg)
        print(msg) # will redirect to cron_tasks.log file, by the parent script
