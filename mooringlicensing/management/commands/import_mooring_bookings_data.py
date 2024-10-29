from django.core.management.base import BaseCommand
from mooringlicensing.components.main.utils import import_mooring_bookings_data
import logging

from mooringlicensing.management.commands.utils import construct_email_message

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')


class Command(BaseCommand):
    help = 'Import Mooring Bookings data'

    def handle(self, *args, **options):
        errors, updates = import_mooring_bookings_data()

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)

