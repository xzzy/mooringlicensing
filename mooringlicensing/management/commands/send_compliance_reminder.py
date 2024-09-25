from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.conf import settings
from mooringlicensing.components.compliances.models import Compliance, ComplianceUserAction
from mooringlicensing.components.main.models import NumberOfDaysType, NumberOfDaysSetting
from django.core.exceptions import ImproperlyConfigured
from mooringlicensing.settings import CODE_DAYS_FOR_FIRST_REMINDER, CODE_DAYS_FOR_SECOND_REMINDER, CODE_DAYS_FOR_FINAL_REMINDER, CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA
from mooringlicensing.components.compliances.email import (
                        send_reminder_email_notification,
                        send_internal_reminder_email_notification,
                        send_due_email_notification,
                        send_internal_due_email_notification
                        )
import logging

from mooringlicensing.management.commands.utils import construct_email_message

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')


class Command(BaseCommand):
    help = 'Send notification emails for compliances which has past due dates, and also reminder notification emails for those that are within the daterange prior to due_date (eg. within 14 days of due date)'

    def clean_old_days_settings():
        try:
            old_settings = NumberOfDaysType.objects.filter(description__icontains = 'accept the MLA offer')
            for setting in old_settings:
                setting.delete()
        except:
            print("Settings Already cleaned")
    
    def handle(self, *args, **options):
        today = timezone.localtime(timezone.now()).date()
        Command.clean_old_days_settings() #this function is used just to clean the "NumberOfDaysSetting" model as the old entries has been modified. 
        #TODO: remove this function after the days settings are cleaned in dev 
        errors = []
        updates = []
        logger.info('Running command {}'.format(__name__))
        days_type_first_reminder = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_FIRST_REMINDER)
        days_setting_first_reminder = NumberOfDaysSetting.get_setting_by_date(days_type_first_reminder, today)
        if not days_setting_first_reminder:
            raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type_first_reminder.name, today))
        
        days_type_second_reminder = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_SECOND_REMINDER)
        days_setting_second_reminder = NumberOfDaysSetting.get_setting_by_date(days_type_second_reminder, today)
        if not days_setting_second_reminder:
            raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type_second_reminder.name, today))

        days_type_final_reminder = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_FINAL_REMINDER)
        days_setting_final_reminder = NumberOfDaysSetting.get_setting_by_date(days_type_final_reminder, today)
        if not days_setting_final_reminder:
            raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type_final_reminder.name, today))

        days_first_reminder = days_setting_first_reminder.number_of_days
        days_second_reminder = days_setting_second_reminder.number_of_days
        days_final_reminder = days_setting_final_reminder.number_of_days
        due_date_first = today + timedelta(days=days_first_reminder)
        due_date_second = today + timedelta(days=days_second_reminder) 
        due_date_final = today + timedelta(days=days_final_reminder)
        
        queries = Q()
        queries &= Q(processing_status = Compliance.PROCESSING_STATUS_DUE)
        queries &= (Q(due_date=due_date_first) | Q(due_date=due_date_second) | Q(due_date=due_date_final))
        compliance_due_reminder = Compliance.objects.filter(queries)

        queries = Q()
        queries &= Q(processing_status = Compliance.PROCESSING_STATUS_OVERDUE)
        queries &= Q(post_reminder_sent = False)
        compliance_overdue_reminder = Compliance.objects.filter(queries)
                
        for c in compliance_due_reminder:
            with transaction.atomic():
                try:
                    send_due_email_notification(c)
                    send_internal_due_email_notification(c)
                    c.due_reminder_count+=1
                    c.save()
                    updates.append(c.lodgement_number)
                    logger.info('Reminder sent for due compliance {}'.format(c.lodgement_number))
                    ComplianceUserAction.log_action(c, ComplianceUserAction.ACTION_REMINDER_SENT.format(c.id),user=None)
                    logger.info('Reminder sent for due compliance {} '.format(c.lodgement_number))
                except Exception as e:
                    err_msg = 'Error sending Reminder Compliance {}'.format(c.lodgement_number)
                    logger.error('{}\n{}'.format(err_msg, str(e)))
                    errors.append(err_msg)
                    
        for c in compliance_overdue_reminder:
            with transaction.atomic():
                try:
                    send_reminder_email_notification(c)
                    send_internal_reminder_email_notification(c)
                    c.post_reminder_sent = True
                    c.save()
                    updates.append(c.lodgement_number)
                    ComplianceUserAction.log_action(c, ComplianceUserAction.ACTION_OVERDUE_REMINDER_SENT.format(c.id),user=None)
                    logger.info('Post due date reminder sent for Compliance {} '.format(c.lodgement_number))
                except Exception as e:
                    err_msg = 'Error sending Overdue Compliance Reminder {}'.format(c.lodgement_number)
                    logger.error('{}\n{}'.format(err_msg, str(e)))
                    errors.append(err_msg)
        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        # err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(errors)>0 else '<strong style="color: green;">Errors: 0</strong>'
        # msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)
