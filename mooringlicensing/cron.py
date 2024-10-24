from datetime import date, timedelta

from django.db.models import Q
from django.core import management
from django_cron import CronJobBase, Schedule
from django.conf import settings

#from mooringlicensing.components.main.api import oracle_integration

#TODO does not appear to be in use- remove
class OracleIntegrationCronJob(CronJobBase):
    """
    To Test (shortly after RUN_AT_TIMES):
        ./manage_ml.py runcrons
    """
    RUN_AT_TIMES = [settings.CRON_RUN_AT_TIMES]

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'ml.oracle_integration'

    def do(self):
        pass
        #oracle_integration(str(date.today()-timedelta(days=1)),False)

