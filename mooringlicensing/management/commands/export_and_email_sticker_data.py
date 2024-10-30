import logging
from django.core.management.base import BaseCommand
from mooringlicensing.components.approvals.models import Approval
from mooringlicensing.components.main.utils import sticker_export, email_stickers_document, reorder_wla
from mooringlicensing.components.proposals.models import Mooring
from mooringlicensing.management.commands.utils import construct_email_message

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')


class Command(BaseCommand):
    help = 'Export and email sticker data'

    def handle(self, *args, **options):
        # 1. Export sticker details as a spreadsheet file
        updates, errors = sticker_export()

        # 2. Email the file generated above to the sticker company
        success_filenames, error_filenames = email_stickers_document()

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)