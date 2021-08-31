import csv
from datetime import datetime
import pytz
import os
from ledger.settings_base import TIME_ZONE
from mooringlicensing.settings import BASE_DIR
from mooringlicensing.components.approvals.models import (
        Approval, WaitingListAllocation, AnnualAdmissionPermit, 
        AuthorisedUserPermit, MooringLicence
        )


date_now = datetime.now(pytz.timezone(TIME_ZONE)).date()
date_now_str = date_now.strftime('%Y%m%d')

def write_wla():
    approval_type = WaitingListAllocation.code
    approvals = WaitingListAllocation.objects.filter(status='current')
    header_row = []
    rows = [[wla.lodgement_number] for wla in WaitingListAllocation.objects.filter(status='current')]
    write_file(approval_type, approvals, header_row, rows)

def write_aap():
    approval_type = AnnualAdmissionPermit.code
    approvals = AnnualAdmissionPermit.objects.filter(status='current')
    header_row = []
    rows = [[aap.lodgement_number] for aap in AnnualAdmissionPermit.objects.filter(status='current')]
    write_file(approval_type, approvals, header_row, rows)

def write_aup():
    approval_type = AuthorisedUserPermit.code
    approvals = AuthorisedUserPermit.objects.filter(status='current')
    header_row = []
    rows = [[aup.lodgement_number] for aup in AuthorisedUserPermit.objects.filter(status='current')]
    write_file(approval_type, approvals, header_row, rows)

def write_ml():
    approval_type = MooringLicence.code
    approvals = MooringLicence.objects.filter(status='current')
    header_row = []
    rows = [[ml.lodgement_number] for ml in MooringLicence.objects.filter(status='current')]
    write_file(approval_type, approvals, header_row, rows)

def write_file(approval_type, approvals, header_row, rows):
    filename = os.path.join(BASE_DIR, 'mooringlicensing', 'utils', 'csv', '{}_{}.csv'.format(approval_type, date_now_str))

    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=':', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(header_row)
        for row in rows:
            csvwriter.writerow(row)

write_wla()
write_aap()
write_aup()
write_ml()

