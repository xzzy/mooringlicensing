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
    header_row = ['Lodgement Number', 'Start Date', 'Expiry Date', 'Issue Date', 'WLA Queue Date', 'WLA Order',
            'First Name', 'Last Name', 'Address 1', 'Suburb', 'State', 'Country', 'Postcode', 'Postal Address',
            'Phone', 'Mobile', 'EMAIL', 'Vessel Rego', 'Company',
    ]
    rows = [[wla.lodgement_number, wla.start_date, wla.expiry_date, wla.issue_date.strftime('%Y-%m-%d'), 
        wla.wla_queue_date.strftime('%Y-%m-%d') if wla.wla_queue_date else '', wla.wla_order,
        wla.submitter.first_name, wla.submitter.last_name, wla.submitter.residential_address.line1,
        wla.submitter.residential_address.locality, wla.submitter.residential_address.state,
        wla.submitter.residential_address.country, wla.submitter.residential_address.postcode, '',
        wla.submitter.phone_number, wla.submitter.mobile_number, wla.submitter.email,
        wla.current_proposal.vessel_ownership.vessel.rego_no if wla.current_proposal.vessel_ownership else '', '',
        ] for wla in WaitingListAllocation.objects.filter(status='current')]
    write_file(approval_type, approvals, header_row, rows)

def write_aap():
    approval_type = AnnualAdmissionPermit.code
    approvals = AnnualAdmissionPermit.objects.filter(status='current')
    header_row = ['Lodgement Number', 'Start Date', 'Expiry Date', 'Issue Date', 'First Name', 
            'Last Name', 'Address 1', 'Suburb', 'State', 'Country', 'Postcode', 'Postal Address',
            'Phone', 'Mobile', 'EMAIL', 'Vessel Rego', 'Company',
    ]
    rows = [[aap.lodgement_number, aap.start_date, aap.expiry_date, aap.issue_date.strftime('%Y-%m-%d'), 
        aap.submitter.first_name, aap.submitter.last_name, aap.submitter.residential_address.line1,
        aap.submitter.residential_address.locality, aap.submitter.residential_address.state,
        aap.submitter.residential_address.country, aap.submitter.residential_address.postcode, '',
        aap.submitter.phone_number, aap.submitter.mobile_number, aap.submitter.email,
        aap.current_proposal.vessel_ownership.vessel.rego_no if aap.current_proposal.vessel_ownership else '', '',
        ] for aap in AnnualAdmissionPermit.objects.filter(status='current')]
    write_file(approval_type, approvals, header_row, rows)

def write_aup():
    approval_type = AuthorisedUserPermit.code
    approvals = AuthorisedUserPermit.objects.filter(status='current')
    header_row = ['Lodgement Number', 'Start Date', 'Expiry Date', 'Issue Date', 'Moorings', 'First Name', 
            'Last Name', 'Address 1', 'Suburb', 'State', 'Country', 'Postcode', 'Postal Address',
            'Phone', 'Mobile', 'EMAIL', 'Vessel Rego', 'Company',
    ]
    rows = [[aup.lodgement_number, aup.start_date, aup.expiry_date, aup.issue_date.strftime('%Y-%m-%d'), 
        ','.join(str(moa.mooring) for moa in aup.mooringonapproval_set.filter(mooring__mooring_licence__status='current')),
        aup.submitter.first_name, aup.submitter.last_name, aup.submitter.residential_address.line1,
        aup.submitter.residential_address.locality, aup.submitter.residential_address.state,
        aup.submitter.residential_address.country, aup.submitter.residential_address.postcode, '',
        aup.submitter.phone_number, aup.submitter.mobile_number, aup.submitter.email,
        aup.current_proposal.vessel_ownership.vessel.rego_no if aup.current_proposal.vessel_ownership else '', '',
        ] for aup in AuthorisedUserPermit.objects.filter(status='current')]
    write_file(approval_type, approvals, header_row, rows)

def write_ml():
    approval_type = MooringLicence.code
    approvals = MooringLicence.objects.filter(status='current')
    header_row = ['Lodgement Number', 'Start Date', 'Expiry Date', 'Issue Date', 'Mooring', 'First Name', 
            'Last Name', 'Address 1', 'Suburb', 'State', 'Country', 'Postcode', 'Postal Address',
            'Phone', 'Mobile', 'EMAIL', 'Vessels',
    ]
    rows = [[ml.lodgement_number, ml.start_date, ml.expiry_date, ml.issue_date.strftime('%Y-%m-%d'), 
        ml.mooring if hasattr(ml, 'mooring') else '',
        ml.submitter.first_name, ml.submitter.last_name, ml.submitter.residential_address.line1,
        ml.submitter.residential_address.locality, ml.submitter.residential_address.state,
        ml.submitter.residential_address.country, ml.submitter.residential_address.postcode, '',
        ml.submitter.phone_number, ml.submitter.mobile_number, ml.submitter.email,
        ','.join(vessel.rego_no for vessel in ml.vessel_list),
        ] for ml in MooringLicence.objects.filter(status='current')]
    write_file(approval_type, approvals, header_row, rows)

def write_file(approval_type, approvals, header_row, rows):
    if not os.path.isdir(os.path.join(BASE_DIR, 'mooringlicensing', 'utils', 'csv')):
        os.mkdir(os.path.join(BASE_DIR, 'mooringlicensing', 'utils', 'csv'))
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

