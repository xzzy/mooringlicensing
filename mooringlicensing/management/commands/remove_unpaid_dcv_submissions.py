import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.models import Q

import logging
from mooringlicensing.components.approvals.models import DcvAdmission, DcvPermit
from mooringlicensing.management.commands.utils import construct_email_message

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')

class Command(BaseCommand):
    help = 'Remove Unpaid DCV admission and permit applications which has been created before 24 hours'
    
    def handle(self, *args, **options):
        logger.info('Running command {}'.format(__name__))
        today = timezone.localtime(timezone.now())
        errors = []
        updates = []
        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        removal_date = today - datetime.timedelta(hours=24) 
        queryset=Q()
        queryset = DcvAdmission.objects.filter(Q(status=DcvAdmission.DCV_ADMISSION_STATUS_UNPAID) & Q(date_created__lt = removal_date))
        for admission in queryset:
            try:
                admission.status = DcvAdmission.DCV_ADMISSION_STATUS_CANCELLED
                admission.save()
                logger.info('Updated DCV Admission {} status to {}'.format(admission.id, admission.status))
                updates.append(admission.lodgement_number)
            except Exception as e:
                err_msg = 'Error updating DCV Admission {} status'.format(admission.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)

        queryset=Q()
        queryset = DcvPermit.objects.filter(Q(lodgement_datetime=None) & Q(date_created__lt = removal_date) & Q(migrated=False))
        for permit in queryset:
            try:
                permit.status = DcvPermit.DCV_PERMIT_STATUS_CANCELLED
                permit.save()
                logger.info('Updated DCV Permit {} status to {}'.format(permit.id, permit.status))
                updates.append(permit.lodgement_number)
            except Exception as e:
                err_msg = 'Error updating DCV Permit {} status'.format(permit.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)                
            
        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)
        
