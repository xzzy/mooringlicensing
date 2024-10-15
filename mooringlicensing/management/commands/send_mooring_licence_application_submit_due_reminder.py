from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q

import logging

from mooringlicensing.components.proposals.email import send_invitee_reminder_email
from mooringlicensing.components.approvals.models import Approval, WaitingListAllocation, MooringLicence
from mooringlicensing.components.main.models import NumberOfDaysType, NumberOfDaysSetting
from mooringlicensing.management.commands.utils import construct_email_message
from mooringlicensing.settings import CODE_DAYS_FOR_FIRST_REMINDER, CODE_DAYS_FOR_SECOND_REMINDER, CODE_DAYS_FOR_FINAL_REMINDER, CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')


class Command(BaseCommand):
    help = 'Send an email to remind the WLA to accept the offered mooring licence before the offer expires'

    def handle(self, *args, **options):
        today = timezone.localtime(timezone.now()).date()

        self.perform(WaitingListAllocation.code, today, **options)
        self.perform(MooringLicence.code, today, **options)

    def perform(self, approval_type, today, **options):
        errors = []
        updates = []

        #Retrieve the date for which reminder email need to be sent
        if approval_type == WaitingListAllocation.code:
            approval_class = WaitingListAllocation
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

            days_type_total_period = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA)
            days_setting_total_period = NumberOfDaysSetting.get_setting_by_date(days_type_total_period, today)
            if not days_setting_total_period:
                raise ImproperlyConfigured("NumberOfDays: {} is not defined for the date: {}".format(days_type_total_period.name, today))
        else:
            # Do nothing
            return
        days_first_reminder = days_setting_first_reminder.number_of_days
        days_second_reminder = days_setting_second_reminder.number_of_days
        days_final_reminder = days_setting_final_reminder.number_of_days
        total_expire_period = days_setting_total_period.number_of_days
        
        notification_date_first = today + timedelta(days=days_first_reminder-total_expire_period)
        notification_date_second = today + timedelta(days=days_second_reminder-total_expire_period) 
        notification_date_final = today + timedelta(days=days_final_reminder-total_expire_period) 
        logger.info('Running command {}'.format(__name__))

        # Get approvals
        if approval_type == WaitingListAllocation.code:
            queries = Q()
            queries &= Q(status=Approval.APPROVAL_STATUS_CURRENT)
            queries &= Q(internal_status=Approval.INTERNAL_STATUS_OFFERED)
            queries &= (Q(issue_date__date=notification_date_first) | Q(issue_date__date=notification_date_second) | Q(issue_date__date=notification_date_final))
            approvals = approval_class.objects.filter(queries)
           
        for a in approvals:
            try:
                proposal = a.current_proposal
                today = timezone.localtime(timezone.now())
                if(proposal.invitee_reminder_date is None or proposal.invitee_reminder_date.date() != today.date()):
                    due_date = a.issue_date + timedelta(total_expire_period)
                    send_invitee_reminder_email(a, due_date)
                    proposal.invitee_reminder_sent = True
                    proposal.invitee_reminder_date = today
                    a.save()
                    proposal.save()
                    updates.append(a.lodgement_number)
                    logger.info('Reminder to permission holder sent for Approval {}'.format(a.lodgement_number))
            except Exception as e:
                err_msg = 'Error sending reminder to permission holder for Approval {}'.format(a.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)
       

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        # err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(
        #     errors) > 0 else '<strong style="color: green;">Errors: 0</strong>'
        # msg = '<p>{} ({}) completed. {}. IDs updated: {}.</p>'.format(cmd_name, approval_type, err_str, updates)
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)
