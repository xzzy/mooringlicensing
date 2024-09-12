from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q

import logging

from mooringlicensing.components.approvals.email import send_reminder_to_accept_ml_offer_mail
from mooringlicensing.components.approvals.models import Approval, WaitingListAllocation, MooringLicence
from mooringlicensing.components.main.models import NumberOfDaysType, NumberOfDaysSetting
from mooringlicensing.management.commands.utils import construct_email_message
from mooringlicensing.settings import CODE_DAYS_FOR_FIRST_REMINDER_BEFORE_MLA_EXPIRE, CODE_DAYS_FOR_SECOND_REMINDER_BEFORE_MLA_EXPIRE, CODE_DAYS_FOR_FINAL_REMINDER_BEFORE_MLA_EXPIRE, CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')


class Command(BaseCommand):
    help = 'Send an email to remind the WLA to accept the offered mooring licence before the offer expires'

    def handle(self, *args, **options):
        today = timezone.localtime(timezone.now()).date()

        self.perform(WaitingListAllocation.code, today, **options)
        self.perform(MooringLicence.code, today, **options)
        # self.perform(AuthorisedUserPermit.code, today, **options)

    def perform(self, approval_type, today, **options):
        errors = []
        updates = []

        #Retrieve the date for which reminder email need to be sent
        if approval_type == WaitingListAllocation.code:
            approval_class = WaitingListAllocation
            days_type_expire_period_first = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_FIRST_REMINDER_BEFORE_MLA_EXPIRE)
            days_setting_expire_period_first = NumberOfDaysSetting.get_setting_by_date(days_type_expire_period_first, today)
            if not days_setting_expire_period_first:
                raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type_expire_period_first.name, today))
            
            days_type_expire_period_second = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_SECOND_REMINDER_BEFORE_MLA_EXPIRE)
            days_setting_expire_period_second = NumberOfDaysSetting.get_setting_by_date(days_type_expire_period_second, today)
            if not days_setting_expire_period_second:
                raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type_expire_period_second.name, today))

            days_type_expire_period_final = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_FINAL_REMINDER_BEFORE_MLA_EXPIRE)
            days_setting_expire_period_final = NumberOfDaysSetting.get_setting_by_date(days_type_expire_period_final, today)
            if not days_setting_expire_period_final:
                raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type_expire_period_first.name, today))

            days_type_total_period = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA)
            days_setting_total_period = NumberOfDaysSetting.get_setting_by_date(days_type_total_period, today)
            if not days_setting_total_period:
                raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type_total_period.name, today))
        else:
            # Do nothing
            return
        days_before_expire_first = days_setting_expire_period_first.number_of_days
        days_before_expire_second = days_setting_expire_period_second.number_of_days
        days_before_expire_final = days_setting_expire_period_final.number_of_days
        total_expire_period = days_setting_total_period.number_of_days
        notification_date_first = today + timedelta(days=days_before_expire_first-total_expire_period)
        notification_date_second = today + timedelta(days=days_before_expire_second-total_expire_period) 
        notification_date_final = today + timedelta(days=days_before_expire_final-total_expire_period) 
        logger.info('Running command {}'.format(__name__))

        # For debug
        # params = options.get('params')
        # debug = True if params.get('debug', 'f').lower() in ['true', 't', 'yes', 'y'] else False
        # approval_lodgement_number = params.get('send_vessel_nominate_reminder_lodgement_number', 'no-number')

        # Get approvals
        if approval_type == WaitingListAllocation.code:
            queries = Q()
            queries &= Q(status=Approval.APPROVAL_STATUS_CURRENT)
            queries &= Q(internal_status=Approval.INTERNAL_STATUS_OFFERED)
            queries &= Q(issue_date__date=notification_date_first)
            queries &= Q(expiry_notice_count=0)
            approval_first_reminder = approval_class.objects.filter(queries)
            
            queries = Q()
            queries &= Q(status=Approval.APPROVAL_STATUS_CURRENT)
            queries &= Q(internal_status=Approval.INTERNAL_STATUS_OFFERED)
            queries &= Q(issue_date__date=notification_date_second)
            queries &= Q(expiry_notice_count=1)
            approval_second_reminder = approval_class.objects.filter(queries)

            queries = Q()
            queries &= Q(status=Approval.APPROVAL_STATUS_CURRENT)
            queries &= Q(internal_status=Approval.INTERNAL_STATUS_OFFERED)
            queries &= Q(issue_date__date=notification_date_final)
            queries &= Q(expiry_notice_count=2)
            approval_final_reminder = approval_class.objects.filter(queries)
        notice_count = 0                
        for a in approval_first_reminder:
            try:
                notice_count = 1
                #TODO send reminder email based on expiry_notice_count
                send_reminder_to_accept_ml_offer_mail(a, days_before_expire_first, total_expire_period, notice_count)
                a.expiry_notice_count+=1
                a.save()
                logger.info('First Reminder to permission holder sent for Approval {}'.format(a.lodgement_number))
            except Exception as e:
                err_msg = 'Error sending first reminder to permission holder for Approval {}'.format(a.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)
        for a in approval_second_reminder:
            try:
                #TODO send reminder email based on expiry_notice_count
                notice_count = 2
                send_reminder_to_accept_ml_offer_mail(a, days_before_expire_second, total_expire_period, notice_count)
                a.expiry_notice_count+=1
                a.save()
                logger.info('Second Reminder to permission holder sent for Approval {}'.format(a.lodgement_number))
            except Exception as e:
                err_msg = 'Error sending second reminder to permission holder for Approval {}'.format(a.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)
        for a in approval_final_reminder:
            try:
                notice_count = 3
                #TODO send reminder email based on expiry_notice_count
                send_reminder_to_accept_ml_offer_mail(a, days_before_expire_final, total_expire_period, notice_count)
                a.expiry_notice_count+=1
                a.save()
                logger.info('Third Reminder to permission holder sent for Approval {}'.format(a.lodgement_number))
            except Exception as e:
                err_msg = 'Error sending third reminder to permission holder for Approval {}'.format(a.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        # err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(
        #     errors) > 0 else '<strong style="color: green;">Errors: 0</strong>'
        # msg = '<p>{} ({}) completed. {}. IDs updated: {}.</p>'.format(cmd_name, approval_type, err_str, updates)
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)
