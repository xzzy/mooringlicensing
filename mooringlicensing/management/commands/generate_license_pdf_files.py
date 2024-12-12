from django.core.management.base import BaseCommand
import logging
from mooringlicensing.components.main.utils import generate_pdf_files
from mooringlicensing.management.commands.utils import construct_email_message

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')

class Command(BaseCommand):
    help = 'Generate License PDF Files'

    def handle(self, *args, **options):
        errors, updates = generate_pdf_files()

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        msg = construct_email_message(cmd_name, errors, updates)
        logger.info(msg)
        cron_email.info(msg)

