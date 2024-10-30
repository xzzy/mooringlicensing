#TODO is this required?
from django.core.management.base import BaseCommand
import logging
from mooringlicensing.utils.export_clean import clean

logger = logging.getLogger(__name__)

LOGFILE = 'logs/run_export_to_mooring_booking_cron_task.log'

class Command(BaseCommand):
    help = 'Run Mooring Licensing Export to Mooring Booking Cron tasks'

    def handle(self, *args, **options):
        src_path = '/data/LotusNotes/2024_02_06'
        out_path = src_path + '/clean'
        clean(srcpath=src_path, outpath=out_path)