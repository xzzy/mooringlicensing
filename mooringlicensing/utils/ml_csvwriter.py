import csv
from datetime import date
from ledger.settings_base import TIME_ZONE


date_now = datetime.now(pytz.timezone(TIME_ZONE)).date()
date_now_str = date_now.strf('%Y%m%d')
print(date_now_str)
#with open(
