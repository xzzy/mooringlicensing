from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from mooringlicensing.components.main.utils import import_mooring_bookings_data
from datetime import date, timedelta

import itertools

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import Mooring Bookings data'

    def handle(self, *args, **options):
        errors, updates = import_mooring_bookings_data()

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(errors)>0 else '<strong style="color: green;">Errors: 0</strong>'
        msg = '<p>{} completed. Errors: {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        logger.info(msg)
        print(msg) # will redirect to cron_tasks.log file, by the parent script

