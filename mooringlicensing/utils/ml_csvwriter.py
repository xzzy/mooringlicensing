import csv
from datetime import datetime
import pytz
import os
from ledger.settings_base import TIME_ZONE
from mooringlicensing.settings import BASE_DIR


date_now = datetime.now(pytz.timezone(TIME_ZONE)).date()
#date_now = datetime.now(pytz.timezone('Australia/Perth')).date()
date_now_str = date_now.strftime('%Y%m%d')
print(date_now_str)
approval_type = 'ml'
filename = os.path.join(BASE_DIR, 'mooringlicensing', 'utils', 'csv', '{}_{}.csv'.format(approval_type, date_now_str))
#filename = os.path.join('.', '{}_{}.csv'.format(approval_type, date_now_str))

with open(filename, 'w', newline='') as csvfile:
    ml_csvwriter = csv.writer(csvfile, delimiter=':', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    ml_csvwriter.writerow(['stuff1', 'stuff2', 'stuff3'])
    ml_csvwriter.writerow(['stuff4', 'stuff5', 'stuff6'])

