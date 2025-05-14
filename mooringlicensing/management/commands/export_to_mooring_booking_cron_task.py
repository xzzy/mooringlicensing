from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from pathlib import Path
import subprocess

import logging
logger = logging.getLogger(__name__)

LOGFILE = 'logs/run_export_to_mooring_booking_cron_task.log'

class Command(BaseCommand):
    help = 'Run Mooring Licensing Export to Mooring Booking Cron tasks'

    def handle(self, *args, **options):
        try:
            stdout_redirect = ' | tee -a {}'.format(LOGFILE)
            subprocess.call('cat /dev/null > {}'.format(LOGFILE), shell=True)  # empty the log file

            logger.info('Running command {}'.format(__name__))
            subprocess.call('python manage_ml.py export_to_mooring_booking' + stdout_redirect, shell=True)

            logger.info('Command {} completed'.format(__name__))
        except:
            self.send_email()

    def send_email(self):
        email_instance = settings.EMAIL_INSTANCE
        log_txt = Path(LOGFILE).read_text()
        subject = '{} - Export to Mooring Booking Cronjob'.format(settings.SYSTEM_NAME_SHORT)
        body = ''
        to = settings.CRON_NOTIFICATION_EMAIL if isinstance(settings.NOTIFICATION_EMAIL, list) else [settings.CRON_NOTIFICATION_EMAIL]
        msg = EmailMultiAlternatives(subject, log_txt, settings.EMAIL_FROM, to,
                headers={'System-Environment': email_instance}
                )
        msg.attach_alternative(log_txt, "text/html")
        msg.send()