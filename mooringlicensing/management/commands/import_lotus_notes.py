from django.core.management.base import BaseCommand
import logging
from mooringlicensing.utils.export_clean import clean
from confy import env

logger = logging.getLogger(__name__)

LOGFILE = 'logs/run_export_to_mooring_booking_cron_task.log'

class Command(BaseCommand):
    help = 'Run Mooring Licensing Export to Mooring Booking Cron tasks'

    def handle(self, *args, **options):
        src_path = env('LOTUS_NOTES_PATH', '/data/data/projects/mooringlicensing/tmp/ml_export')
        out_path = env('MIGRATION_DATA_PATH', '/data/data/projects/mooringlicensing/tmp/clean')
        clean(srcpath=src_path, outpath=out_path)