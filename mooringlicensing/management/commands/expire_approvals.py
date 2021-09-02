from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from mooringlicensing.components.approvals.models import Approval
from ledger.accounts.models import EmailUser

import logging

from mooringlicensing.settings import CRON_EMAIL

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Change the status of Approvals to Expired when past expiry date'

    def handle(self, *args, **options):
        try:
            user = EmailUser.objects.get(email=CRON_EMAIL)
        except:
            user = EmailUser.objects.create(email=CRON_EMAIL, password='')

        errors = []
        updates = []
        today = timezone.localtime(timezone.now()).date()
        logger.info('Running command {}'.format(__name__))

        queries = Q()
        queries &= (Q(status=Approval.APPROVAL_STATUS_CURRENT) & Q(replaced_by__isnull=True))
        queries &= Q(expiry_date__lt=today)

        approvals = Approval.objects.filter(queries)

        for approval in approvals:
            try:
                approval.expire_approval(user)
                # a.save()  # Saved in the above function...?
                logger.info('Updated Approval {} status to {}'.format(approval.id, approval.status))
                updates.append(approval.lodgement_number)
            except Exception as e:
                err_msg = 'Error updating Approval {} status'.format(approval.lodgement_number)
                logger.error('{}\n{}'.format(err_msg, str(e)))
                errors.append(err_msg)

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(errors) > 0 else '<strong style="color: green;">Errors: 0</strong>'
        msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        logger.info(msg)
        print(msg)
