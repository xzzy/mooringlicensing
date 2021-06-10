from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from pathlib import Path
#from commercialoperator.components.approvals.models import Approval
from ledger.accounts.models import EmailUser
import datetime

import itertools
import subprocess

import logging
logger = logging.getLogger(__name__)

#LOGFILE = 'logs/cron_tasks.log'
LOGFILE = 'logs/run_cron_tasks.log'

class Command(BaseCommand):
    help = 'Run Mooring Licensing Cron tasks'

    def handle(self, *args, **options):
        #print("cron tasks")
        stdout_redirect = ' | tee -a {}'.format(LOGFILE)
        subprocess.call('cat /dev/null > {}'.format(LOGFILE), shell=True)  # empty the log file

        logger.info('Running command {}'.format(__name__))
        #subprocess.call('python manage_co.py update_compliance_status' + stdout_redirect, shell=True) 
        #subprocess.call('python manage_co.py send_compliance_reminder' + stdout_redirect, shell=True) 
        #subprocess.call('python manage_co.py update_approval_status' + stdout_redirect, shell=True) 
        #subprocess.call('python manage_co.py expire_approvals' + stdout_redirect, shell=True) 
        #subprocess.call('python manage_co.py approval_renewal_notices' + stdout_redirect, shell=True)
        #subprocess.call('python manage_co.py eclass_expiry_notices' + stdout_redirect, shell=True) 
        #subprocess.call('python manage_co.py eclass_renewal_notices' + stdout_redirect, shell=True) 
        #subprocess.call('python manage_co.py monthly_invoices' + stdout_redirect, shell=True) 
        subprocess.call('python manage_ml.py import_mooring_bookings_data' + stdout_redirect, shell=True) 
        subprocess.call('python manage_ml.py reset_waiting_list_allocations' + stdout_redirect, shell=True) 

        logger.info('Command {} completed'.format(__name__))
        self.send_email()

    def send_email(self):
        log_txt = Path(LOGFILE).read_text()
        subject = '{} - Cronjob'.format(settings.SYSTEM_NAME_SHORT)
        body = ''
        to = settings.CRON_NOTIFICATION_EMAIL if isinstance(settings.NOTIFICATION_EMAIL, list) else [settings.CRON_NOTIFICATION_EMAIL]
        send_mail(subject, body, settings.EMAIL_FROM, to, fail_silently=False, html_message=log_txt)

