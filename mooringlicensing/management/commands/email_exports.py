from django.core.management.base import BaseCommand
import logging
import json
from ledger_api_client.ledger_models import EmailUserRO
from mooringlicensing.helpers import is_internal_user
from mooringlicensing.management.commands.utils import construct_email_message
from mooringlicensing.components.main.utils import exportModelData
from mooringlicensing import settings

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("parameters", type=str)
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):
        if "parameters" in options and "user_id" in options:
            user_id = options["user_id"]
            params = json.loads(options["parameters"])
            try:
                user = EmailUserRO.objects.get(id=user_id)
            except:
                print("Provided user id not valid")
                logger.Error("Provided user id not valid")
                return

            if is_internal_user(user):
                if not ("model" in params and params["model"]):
                    print("No model provided for export")
                    logger.Error("No model provided for export")
                    return
                model = params["model"]
                if not ("format" in params and params["format"]):
                    format = "csv"
                else:
                    format = params["format"]
                if not ("num_records" in params and params["num_records"]):
                    num_records = settings.MAX_NUM_ROWS_MODEL_EXPORT
                else:
                    num_records = params["num_records"]
                if not ("filters" in params and params["filters"]):
                    filters = {}
                else:
                    filters = params["filters"]

                #get records
                export_data = exportModelData(model, format, filters, num_records)

                #email to user

            else:
                print("User not authorised to receive exports")
                logger.Error("User not authorised to receive exports")
                return
