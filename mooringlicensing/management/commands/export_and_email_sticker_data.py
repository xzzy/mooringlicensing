import logging
from django.core.management.base import BaseCommand
from mooringlicensing.components.main.utils import sticker_export, email_stickers_document, reorder_wla
from mooringlicensing.management.commands.utils import construct_email_message

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')


class Command(BaseCommand):
    help = 'Export and email sticker data'

    def handle(self, *args, **options):
        # from mooringlicensing.components.approvals.models import WaitingListAllocation
        # wla = WaitingListAllocation.objects.all()
        # wla.update(wla_order=None)

        # from mooringlicensing.components.proposals.models import MooringBay
        # bays = MooringBay.objects.all()
        # for bay in bays:
        #     reorder_wla(bay)

        # 1. Export sticker details as a spreadsheet file
        updates, errors = sticker_export()

        # 2. Email the file generated above to the sticker company
        success_filenames, error_filenames = email_stickers_document()

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        error_count = len(errors) + len(error_filenames)
        # err_str = '<strong style="color: red;">Errors: {}</strong>'.format(error_count) if error_count else '<strong style="color: green;">Errors: 0</strong>'
        # msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)
