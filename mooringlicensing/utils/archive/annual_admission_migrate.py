import os
import subprocess
import json
import csv
import datetime
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
#from oscar.apps.address.models import Country
#from ledger.accounts.models import EmailUser, Address
from ledger_api_client.ledger_models import EmailUserRO
from mooringlicensing.components.proposals.models import (
    Proposal,
    ProposalType,
    Vessel,
    Owner,
    VesselOwnership,
    VesselDetails,
    AnnualAdmissionApplication,
    ProposalUserAction,
)
from mooringlicensing.components.approvals.models import Approval, ApprovalHistory, AnnualAdmissionPermit


class AnnualAdmissionMigration(object):
    '''
        from mooringlicensing.utils.annual_admission_migrate import AnnualAdmissionMigration
        AnnualAdmissionMigration(test=False)
    '''

    def __init__(self, filename='mooringlicensing/utils/csv/clean/annual_admissions_booking_report.csv', test=False):
        """
        NOTE:
            filename='mooringlicensing/utils/csv/clean/annual_admissions_booking_report.csv' comes from Moorings RIA system (??)
            (https://mooring-ria-internal.dbca.wa.gov.au/dashboard/bookings/annual-admissions/)
        """
        self.filename = filename
        self.test = test

        self.migrate()

    def migrate(self):

        expiry_date = datetime.date(2023,8,31)
        start_date = datetime.date(2022,9,1)

        address_list = []
        user_list = []
        vessel_list = []
        owner_list = []
        ownership_list = []
        details_list = []
        proposal_list = []
        user_action_list = []
        approval_list = []
        approval_history_list = []

        added = []
        errors = []
        count_no_mooring = 0
        idx = -1
        with transaction.atomic():
            with open(self.filename) as csvfile:
                reader = csv.reader(csvfile, delimiter=str('|'))
                header = next(reader) # skip header
                for row in reader:
                    #import ipdb; ipdb.set_trace()
                    if not row[0].startswith('#'):
                        idx += 1

                        ID = row[0]
                        created = row[1].strip()
                        firstname = row[2].strip()
                        lastname = row[3].strip()
                        address1 = row[4].strip()
                        suburb = row[5].strip()
                        state = row[6].strip()
                        postcode = row[7].strip()
                        sticker_no = row[8].strip()
                        rego_no = row[9].strip()
                        email = row[10].lower().strip()
                        mobile_no = row[11].strip()
                        phone_no = row[12].strip()
                        vessel_name = row[13].strip()
                        length = row[14].strip()
                        year = row[15].strip()
                        status = row[16].strip()
                        booking_period = row[17].strip()
                        country = row[18].strip()

#                        if status != 'expired':
#                            # ignore everything, except 'expired' records
#                            continue
#                        elif idx % 50 == 0:
#                            print(f"{idx} {status}")

#                        if status == 'current' and idx % 50 == 0:
#                            print(f"{idx} {status}")
#                        else:
#                            # ignore everything, except 'current' records
#                            continue

                        if idx % 50 == 0:
                            print(f"{idx} {status}")

                        if self.test:
                            continue

                        try:
                            #import ipdb; ipdb.set_trace()

                            vessel_type = 'other'
                            vessel_weight = Decimal( 0.0 )
                            vessel_draft = Decimal( 0.0 )
                            percentage = 100 # force user to set at renewal time

                            address = None
                            try:
                                user = EmailUserRO.objects.get(email=email)
                            except:
                                import ipdb; ipdb.set_trace()
                                logger.warn(f'User not found: {user}')

                            try:
                                vessel = Vessel.objects.get(rego_no=rego_no)
                            except ObjectDoesNotExist:
                                vessel = Vessel.objects.create(rego_no=rego_no)

                            try:
                                owner = Owner.objects.get(emailuser=user)
                            except ObjectDoesNotExist:
                                owner = Owner.objects.create(emailuser=user)

                            try:
                                vessel_ownership = VesselOwnership.objects.get(owner=owner, vessel=vessel)
                            except ObjectDoesNotExist:
                                vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=percentage)

                            try:
                                vessel_details = VesselDetails.objects.get(vessel=vessel)
                            except MultipleObjectsReturned as e:
                                vessel_details = VesselDetails.objects.filter(vessel=vessel)[0]
                            except ObjectDoesNotExist as e:
                                vessel_details = VesselDetails.objects.create(
                                vessel_type=vessel_type,
                                vessel=vessel,
                                vessel_name=vessel_name,
                                vessel_length=length,
                                vessel_draft=vessel_draft,
                                vessel_weight= vessel_weight,
                                berth_mooring=None
                            )

                            proposal=AnnualAdmissionApplication.objects.create(
                                proposal_type=ProposalType.objects.get(code='new'), # new application
                                submitter=user.id,
                                lodgement_date=datetime.datetime.now(datetime.timezone.utc),
                                migrated=True,
                                vessel_details=vessel_details,
                                vessel_ownership=vessel_ownership,
                                rego_no=rego_no,
                                vessel_type=vessel_type,
                                vessel_name=vessel_name,
                                vessel_length=length,
                                vessel_draft=vessel_draft,
                                vessel_weight=vessel_weight,
                                berth_mooring=None, #'home',
                                percentage=percentage,
                                individual_owner=True,
                                processing_status='approved',
                                customer_status='approved',
                                proposed_issuance_approval={
                                    "start_date": start_date.strftime('%d/%m/%Y'),
                                    "expiry_date": expiry_date.strftime('%d/%m/%Y'),
                                    "details": None,
                                    "cc_email": None,
                                },
                            )

                            ua=ProposalUserAction.objects.create(
                                proposal=proposal,
                                who=user.id,
                                what='Annual Admission - Migrated Application',
                            )

                            #approval = WaitingListAllocation.objects.create(
                            approval = AnnualAdmissionPermit.objects.create(
                                status='current',
                                #internal_status=None,
                                current_proposal=proposal,
                                issue_date = datetime.datetime.now(datetime.timezone.utc),
                                #start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').date(),
                                start_date = start_date,
                                expiry_date = expiry_date,
                                submitter=user.id,
                                migrated=True,
                                export_to_mooring_booking=True,
                            )
                            #print(f'wla_order: {position_no}')

                            proposal.approval = approval
                            proposal.save()
                            #proposal.allocated_mooring.mooring_licence = approval
                            #proposal.allocated_mooring.save()

                            approval_history = ApprovalHistory.objects.create(
                                reason='new',
                                approval=approval,
                                vessel_ownership = vessel_ownership,
                                proposal = proposal,
                                #start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').astimezone(datetime.timezone.utc)
                                start_date = start_date,
                            )

                            added.append(proposal.id)

                            user_list.append(user.id)
                            vessel_list.append(vessel.id)
                            owner_list.append(owner.id)
                            ownership_list.append(vessel_ownership.id)
                            details_list.append(vessel_details.id)
                            proposal_list.append(proposal.proposal.id)
                            user_action_list.append(ua.id)
                            approval_list.append(approval.id)
                            approval_history_list.append(approval_history.id)

                        except Exception as e:
                            errors.append(e)
                            #import ipdb; ipdb.set_trace()
                            #raise Exception(str(e))
                            print(f'{e}')
                            continue

        print(f'EmailUser.objects.get(id__in={user_list}).delete()')
        print(f'Vessel.objects.get(id__in={vessel_list}).delete()')
        print(f'Owner.objects.get(id__in={owner_list}).delete()')
        print(f'VesselOwnership.objects.get(id__in={ownership_list}).delete()')
        print(f'VesselDetails.objects.get(id__in={details_list}).delete()')
        print(f'ProposalUserAction.objects.get(id__in={user_action_list}).delete()')
        print(f'WaitingListAllocation.objects.get(id__in={approval_list}).delete()')
        print(f'ApprovalHistory.objects.get(id__in={approval_history_list}).delete()')
        print(f'errors: {errors}')

