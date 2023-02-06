from datetime import date, timedelta

from django.db.models import Q
from django.core import management
from django_cron import CronJobBase, Schedule
from django.conf import settings

#from mooringlicensing.components.payments_ml.utils import oracle_integration
from mooringlicensing.components.main.api import oracle_integration


class OracleIntegrationCronJob(CronJobBase):
    """
    To Test (shortly after RUN_AT_TIMES):
        ./manage_ml.py runcrons
    """
    #RUN_AT_TIMES = '09:39'
    RUN_AT_TIMES = [settings.CRON_RUN_AT_TIMES]
    #RUN_AT_TIMES = [RUN_AT_TIMES]

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'ml.oracle_integration'

    def do(self):
        oracle_integration(str(date.today()-timedelta(days=1)),False)

