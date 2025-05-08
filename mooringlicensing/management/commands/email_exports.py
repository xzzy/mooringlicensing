from django.core.management.base import BaseCommand
import logging

from mooringlicensing.management.commands.utils import construct_email_message

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("parameters", type=str)

    def handle(self, *args, **options):
        print(options["parameters"])
