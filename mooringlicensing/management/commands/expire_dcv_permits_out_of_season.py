import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.models import Q

import logging
from mooringlicensing.components.approvals.models import DcvPermit
from mooringlicensing.management.commands.utils import construct_email_message

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')

class Command(BaseCommand):
    help = 'Set status of DCV Permits that are out of season to Expired'
    
    def handle(self, *args, **options):
        logger.info('Running command {}'.format(__name__))
        today = timezone.localtime(timezone.now())
        errors = []
        updates = []
        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        queryset=Q()

        queryset = DcvPermit.objects.filter(Q(end_date__lt = today))
        for permit in queryset:
            try:
                permit.status = DcvPermit.DCV_PERMIT_STATUS_EXPIRED
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
        
