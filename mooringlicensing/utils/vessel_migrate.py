import os
import subprocess
import json
import ast
import csv
import datetime
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from oscar.apps.address.models import Country
from ledger.accounts.models import EmailUser, Address
from mooringlicensing.components.proposals.models import (
    Proposal,
    Vessel,
    Owner,
    VesselOwnership,
    VesselDetails,
    MooringLicenceApplication,
    ProposalUserAction,
    Mooring,
    MooringBay,
    MooringBay,
)
from mooringlicensing.components.approvals.models import Approval, ApprovalHistory, MooringLicence, VesselOwnershipOnApproval, Sticker



class VesselMigration(object):
    '''
        PRELIM:
            from mooringlicensing.utils.json_to_csv import JsonToCsv
            JsonToCsv().convert()

        from mooringlicensing.utils.authorised_user_migrate import AuthUserPermitMigration, GrepSearch
        AuthUserPermitMigration(test=False)
    '''

    #def __init__(self, path='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes', test=False):
    #def __init__(self, path='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_07Oct2021', path_csv='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_all_csv', test=False):
    def __init__(self, path='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes', test=False):
        self.path = path
        self.path_csv = path + '_all_csv' if not path.endswith('/') else path.strip('/') + '_all_csv'
        self.test = test

#        self.auth_users_with_L = self.read_dict('Auth_Users___Surname___with_L.json')
#        self.auth_users_No_L = self.read_dict('Auth_Users___Surname___No_L.json')
#        self.moorings = self.read_dict('Auth_Users___Surname___Moorings.json')
#        self.vessel_rego = self.read_dict('Auth_Users___Vessel_Rego.json')
#
#        self.canc_lic = self.read_dict('Auth_Users___Cancelled_Lic.json')
#        self.canc = self.read_dict('Auth_Users___Cancelled.json')
#
#        self.vessel_rego_all = self.read_dict('Vessel___Rego___All.json')
#        self.vessel_rego_current = self.read_dict('Vessel___Rego___Current.json')
#        self.vessel_details_all = self.read_dict('Vessel___Details_All.json')
#        self.vessel_details_current = self.read_dict('Vessel___Details_Current.json')
#        self.people_name = self.read_dict('PeopleName.json')

        #self.surname = self.read_dict('Licencees___Surname.json')
        self.mooring_no = self.read_dict('Licencees___Mooring_No.json')
        self.mooring_details = self.read_dict('Mooring_Details.json')
        self.people_lictype = self.read_dict('PeopleLicType.json')
        self.vessel_details = self.read_dict('Vessel___Details_All.json')
        #self.vessel_multiple = self.read_dict('Vessel___Multiple_Vessels.json') # vessel rego and name
        self.vessel_multiple = self.read_dict('Licencees___Sticker_No.json') # vessel rego and name
        self.user_rego = self.read_dict('UserRego.json') # vessel length/draft - if not available in vessel_multiple
        self.user_mooring = self.read_dict('UserMooring.json') # vessel length/draft - if not available in vessel_multiple
        self.people_no = self.read_dict('PeopleNo.json')                        # address/phone details (if no vessel_multiple details)
        self.people_cur_mooring = self.read_dict('People___Current_Mooring.json')                        # address/phone details (if no vessel_multiple details)
        #self.people_email = self.read_dict('People___eMail.json')                        # address/phone details (if no vessel_multiple details)
        self.people_email = self.read_dict('Licencees___Surname.json')                        # address/phone details (if no vessel_multiple details)


        self._auth_users = [
            #... can be found in directory tests/test.json
        ]

        #self.migrate()

    def read_dict(self, fname):
        filename = self.path + os.sep + fname if not self.path.endswith(os.sep) else self.path + fname
        with open(filename) as f:
            f_json = json.load(f)

            # make list unique
            _list = []
            for i in f_json:
                if i not in _list:
                    _list.append(i)

        #import ipdb; ipdb.set_trace()
        return _list

    def search(self, key, value, records):
        for record in records:
            if value == record.get(key):
                return record
        return None

    def search_multiple(self, key, value, records):
        return [record for record in records if value == record.get(key)]


    def get_vessels(self, no_vessel, record):
        if not record:
            # ML with no linked vessel
            #return [('', '', 0.0, 0.0)] # rego/name/length/draft
            return [] # rego/name/length/draft

        #keys = ['_6', '_7', '_8', '_9', '_10']
        ves_keys = ['_10', '_11', '_12', '_13', '_14']
        sticker_keys = ['StickerLNo1', 'StickerLNo2', 'StickerLNo3', 'StickerLNo4', 'StickerLNo5']
        _vessels = []
        for i in range(no_vessel):
            items = record[ves_keys[i]].split('-')
            rego = items[0].strip()
            vessel_name = items[1].strip()
            sticker_no = record[sticker_keys[i]].strip()
            if sticker_no == 'None':
                sticker_no = ''
#                import ipdb; ipdb.set_trace()
            _vessels.append((rego, vessel_name, 0.0, 0.0, sticker_no)) # rego/name/length/draft
        return _vessels

#    def get_stickers(self, no_vessel, record):
#        if not record:
#            # ML with no linked vessel
#            return []
#
#        keys = ['StickerLNo1', 'StickerLNo2', 'StickerLNo3', 'StickerLNo4', 'StickerLNo5']
#        _stickers = []
#        for i in range(no_vessel):
#            sticker_no = record[keys[i]].strip()
#            _stickers.append((rego, vessel_name, 0.0, 0.0)) # rego/name/length/draft
#        return _vessels


    def to_float(self, val):
        try:
            return float(val)
        except Exception as e:
            return 0.0


    def migrate(self):

        #submitter = EmailUser.objects.get(email='jawaid.mushtaq@dbca.wa.gov.au')
        expiry_date = datetime.date(2023,8,31)
        start_date = datetime.date(2022,8,31)
        date_applied = '2022-08-31'
        date_invited = None #date_invited,
        migrated = False

        self.num_vessels = []
        self.vessels_found = []
        self.vessels_not_found = []
        self.vessel_details_not_found = []
        self.emailuser = []
        self.errors = []
        self.approvals = []

        user_data = []
        vessel_data = []
        mla_data = []
        ml_all_data = []
        user_data.append(['PersNo', 'Email', 'DoB', 'FirstName', 'LastName', 'MobileNo', 'PhoneNo', 'Address', 'NoVessel'])
        vessel_data.append(['Owner', 'Email', 'DoB', 'Rego No', 'DoT Name', 'Percentage Ownership', 'Vessel Type', 'Vessel Name', 'Length', 'Draft', 'Weight', 'berth_mooring'])
        mla_data.append(['PersNo', 'Email', 'DoB', 'Rego No', 'MooringNo', 'Date Invited'])
        ml_all_data.append(['PersNo', 'Email', 'DoB', 'DoB', 'FirstName', 'LastName', 'MobileNo', 'PhoneNo', 'Address', 'Rego No', 'DoT Name', 'Percentage Ownership', 'Vessel Type', 'Vessel Name', 'Length', 'Draft', 'Weight', 'berth_mooring', 'MooringNo', 'Date Invited'])

        rego_no=''
        dot_name=''
        percentage=''
        vessel_type=''
        vessel_name=''
        vessel_overall_length=''
        vessel_draft=''
        vessel_weight=''
        berth_mooring=''

        with transaction.atomic():
            #for idx, record in enumerate(self.moorings[827:], 827):
            import ipdb; ipdb.set_trace()
            #for idx, record in enumerate(self.vessel_rego_current[:60], 0):
            #for idx, record in enumerate(self.vessel_rego_current, 0):
            #for idx, record in enumerate(self.mooring_no[:300], 0):
            #for idx, record in enumerate(self.mooring_no[200:205], 0):
            for idx, record in enumerate(self.mooring_no[0:], 0):
                try:
                    mooring_no  = record['MooringNo']
                    username = record['UserName']
                    pers_no  = record['PersNo']
                    address = record['_1']
                    no_vessel = int(float(record['NoVessel']))

                    if no_vessel>5:
                        self.num_vessels.append(dict(username=username, pers_no=pers_no, no_vessel=no_vessel, mooring_no=mooring_no))
                        no_vessel = 5 # ignore the remainder (JSON file only list max. 5)

                    if pers_no not in ['000477', '206776', '207209', '030742']:
                        continue
#                    if pers_no == '073604':
#                        import ipdb; ipdb.set_trace()
#                    else:
#                        continue



                    # assume first vessel is licenced to Mooring
                    record_ves_details = self.search('PersNo', pers_no, self.vessel_multiple)
                    vessels = self.get_vessels(no_vessel, record_ves_details)
                    print(f'{idx} Vessel details found: {username} {pers_no} {mooring_no} {no_vessel} {vessels}')          
                    #vessel_mooring = vessels[0]

                    #import ipdb; ipdb.set_trace()
                    record_people_no = self.search('PersNo', pers_no, self.people_cur_mooring)
                    address = record_people_no['_1']
                    phone_home = record_people_no['PhoneHome']
                    phone_mobile = record_people_no['PhoneMobile']
                    phone_work = record_people_no['PhoneWork']

                    #{'LastName': 'Abbott', '_7': 'William', 'PersNo': '207907', '_8': 'W', 'NoVessel': '1', '_9': '1', 'EMail': 'wabbinator@gmail.com', 'LicContactEmail': 'None'}
                    record_people_email = self.search('PersNo', pers_no, self.people_email)
                    email = record_people_email['EMail'].split(';')[0].strip().lower()

                    user = self.set_emailuser(username, email, address, phone_mobile, phone_home)

                    # see mooringlicensing/utils/tests/mooring_names.txt
                    if Mooring.objects.filter(name=mooring_no).count()>0:
                        mooring = Mooring.objects.filter(name=mooring_no)[0]
                    else:
                        import ipdb; ipdb.set_trace()
                        print(f'Mooring not found: {mooring}')
                        self.errors.append(dict(idx=idx, record=record))
                        continue

                    approval = MooringLicence.objects.create(
                        status='current',
                        #internal_status=None,
                        #current_proposal=proposal,
                        issue_date = datetime.datetime.now(datetime.timezone.utc),
                        #start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').date(),
                        start_date = start_date,
                        expiry_date = expiry_date,
                        submitter=user,
                        migrated=migrated,
                        export_to_mooring_booking=True,
                    )
                    self.approvals.append(approval.id)

                    if not vessels:
                        proposal=MooringLicenceApplication.objects.create(
                            proposal_type_id=1, # new application
                            submitter=user,
                            lodgement_date=datetime.datetime.now(datetime.timezone.utc),
                            migrated=migrated,

                            preferred_bay= mooring.mooring_bay,
                            processing_status='approved',
                            customer_status='approved',
                            allocated_mooring=mooring,
                            proposed_issuance_approval={
                                "start_date": start_date.strftime('%d/%m/%Y'),
                                "expiry_date": expiry_date.strftime('%d/%m/%Y'),
                                "details": None,
                                "cc_email": None,
                                "mooring_id": mooring.id,
                                "ria_mooring_name": mooring.name,
                                "mooring_bay_id": mooring.mooring_bay.id,
    
                                "vessel_ownership": [dict(dot_name=i[0]) for i in vessels],
                                "mooring_on_approval": []
                            },
                            date_invited=date_invited,
                        )

                        approval.current_proposal=proposal
                        approval.save()

                    else:
                        #import ipdb; ipdb.set_trace()
                        vessel_objs = []
                        #proposal = None
                        for ves_idx, ves in enumerate(vessels):
                            ves_rego_no = ves[0]
                            ves_name    = ves[1]
                            ves_length  = self.to_float(ves[2])
                            ves_draft   = self.to_float(ves[3])
                            sticker_no  = ves[4]
                            ves_type = ''
                            ves_weight = Decimal( 0.0 )
                            berth_mooring = ''
                            percentage = None # force user to set at renewal time
                            vessel_type = ''

                            try:
                                vessel = Vessel.objects.get(rego_no=ves_rego_no)
                            except ObjectDoesNotExist:
                                vessel = Vessel.objects.create(rego_no=ves_rego_no)

                            try:
                                owner = Owner.objects.get(emailuser=user)
                            except ObjectDoesNotExist:
                                owner = Owner.objects.create(emailuser=user)

                            try:
                                vessel_ownership = VesselOwnership.objects.get(owner=owner, vessel=vessel)
                                vessel_ownership.dot_name = ves_rego_no # rego_no
                                vessel_ownership.save()
                            except ObjectDoesNotExist:
                                #vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=percentage, dot_name=dot_name)
                                vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=percentage, dot_name=ves_rego_no)

                            if VesselDetails.objects.filter(vessel=vessel).count()>0:
                                vessel_details = VesselDetails.objects.filter(vessel=vessel)[0]
                            else:
                                vessel_details = VesselDetails.objects.create(
                                    vessel_type=vessel_type,
                                    vessel=vessel,
                                    vessel_name=ves_name,
                                    vessel_length=ves_length,
                                    vessel_draft=ves_draft,
                                    vessel_weight= ves_weight,
                                    berth_mooring=berth_mooring
                                )

                            vessel_objs.append(dict(
                                vessel=vessel,
                                owner=owner,
                                vessel_ownership=vessel_ownership,
                                vessel_details=vessel_details,
                            ))


                            try:
                                start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').astimezone(datetime.timezone.utc)
                            except:
                                start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d').astimezone(datetime.timezone.utc)


                            #import ipdb; ipdb.set_trace()
                            proposal=MooringLicenceApplication.objects.create(
                                proposal_type_id=1, # new application
                                submitter=user,
                                lodgement_date=datetime.datetime.now(datetime.timezone.utc),
                                migrated=migrated,

                                vessel_details=vessel_details,
                                vessel_ownership=vessel_ownership,
                                rego_no=ves_rego_no,
                                vessel_type=ves_type,
                                vessel_name=ves_name,
                                vessel_length=ves_length,
                                vessel_draft=ves_draft,
                                #vessel_beam='',
                                vessel_weight=ves_weight,
                                berth_mooring=berth_mooring,
                                percentage=percentage,
                                individual_owner=True,
                                dot_name='', #vessel_mooring[0], #vessel_dot,

                                preferred_bay= mooring.mooring_bay,
                                #proposed_issuance_approval={},
                                processing_status='approved',
                                customer_status='approved',
                                allocated_mooring=mooring,
                                proposed_issuance_approval={
                                    "start_date": start_date.strftime('%d/%m/%Y'),
                                    "expiry_date": expiry_date.strftime('%d/%m/%Y'),
                                    "details": None,
                                    "cc_email": None,
                                    "mooring_id": mooring.id,
                                    "ria_mooring_name": mooring.name,
                                    "mooring_bay_id": mooring.mooring_bay.id,
        #                            "vessel_ownership": [{
        #                                    "dot_name": vessel_mooring[0], # vessel_mooring[0] --> rego_no #vessel_dot
        #                                }],
                                    "vessel_ownership": [dict(dot_name=i[0]) for i in vessels],
                                    "mooring_on_approval": []
                                },
                                date_invited=date_invited,
                            )

#                            proposal.vessel_details=vessel_details
#                            proposal.vessel_ownership=vessel_ownership
#                            proposal.rego_no=ves_rego_no
#                            proposal.vessel_type=ves_type
#                            proposal.vessel_name=ves_name
#                            proposal.vessel_length=ves_length
#                            proposal.vessel_draft=ves_draft
#                            #proposal.vessel_beam=''
#                            proposal.vessel_weight=ves_weight
#                            proposal.berth_mooring=berth_mooring
#                            proposal.percentage=percentage
#                            proposal.individual_owner=True
#                            proposal.dot_name='' #vessel_mooring[0], #vessel_dot,
#                            proposal.save()

                            sticker=Sticker.objects.create(
                                number=sticker_no,
                                status='current',
                                approval=approval,
                                printing_date=start_date,
                                mailing_date=start_date,
                                vessel_ownership=vessel_ownership,
                                proposal_initiated=proposal,
                                #dcv_permit=null,
                            )

                            ua=ProposalUserAction.objects.create(
                                proposal=proposal,
                                who=user,
                                what='Mooring Site Licence - Migrated Application',
                            )

                            vooa = VesselOwnershipOnApproval.objects.create(
                                approval=approval,
                                vessel_ownership=vessel_ownership,
                            )

                            #import ipdb; ipdb.set_trace()
                            approval_history = ApprovalHistory.objects.create(
                                reason='new',
                                approval=approval,
                                vessel_ownership=vessel_ownership,
                                proposal = proposal,
                                #start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').astimezone(datetime.timezone.utc)
                                start_date = start_date,
                                #stickers = [sticker.id],
                            )
                            approval_history.stickers.add(sticker.id),

#                    for approval_id in self.approvals:
#                        a = MooringLicence.objects.get(id=approval_id)
#                        import ipdb; ipdb.set_trace()
#                        a.generate_doc()


                    proposal.approval = approval
                    proposal.save()
                    #proposal.allocated_mooring.mooring_licence = approval
                    #proposal.allocated_mooring.save()
                    #approval.generate_doc()

#                    moa = MooringOnApproval.objects.create(
#                        approval=approval,
#                        mooring=mooring,
#                        sticker=None,
#                        site_licensee=True, # ???
#                        end_date=expiry_date
#                    )

                    ml_all_data.append([pers_no, email, user.dob, user.first_name, user.last_name, user.mobile_number, user.phone_number, user.residential_address, rego_no, dot_name, percentage, vessel_type, vessel_name, vessel_overall_length, vessel_draft, vessel_weight, berth_mooring, mooring.name, date_invited])

                    user_data.append([pers_no, email, user.dob, user.first_name, user.last_name, user.mobile_number, user.phone_number, user.residential_address, no_vessel])

                    berth_mooring = ''
                    vessel_data.append([pers_no, email, user.dob, rego_no, dot_name, percentage, vessel_type, vessel_name, vessel_overall_length, vessel_draft, vessel_weight, berth_mooring])

                    #date_invited = ''
                    mla_data.append([pers_no, email, user.dob, rego_no, mooring.name, date_invited])

                except Exception as e:
                    self.errors.append(f'{idx} {record}\n{e}')
                    import ipdb; ipdb.set_trace()
                    print(e)

        #import ipdb; ipdb.set_trace()
        with open('ml_all.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(ml_all_data)

        with open('user.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(user_data)

        with open('vessel.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(vessel_data)

        with open('mla.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(mla_data)





        print(f'vessels_found: {self.vessels_found}')
        print(f'vessels_not_found: {self.vessels_not_found}')
        print(f'vessel_details_not_found: {self.vessel_details_not_found}')
        print(f'num_vessels: {self.num_vessels}')
        print(f'errors: {self.errors}')
        print(f'no. vessels_found: {len(self.vessels_found)}')
        print(f'no. vessels_not_found: {len(self.vessels_not_found)}')
        print(f'no. vessel_details_not_found: {len(self.vessel_details_not_found)}')
        print(f'no. emailuser: {len(self.emailuser)}')
        print(f'no. num_vessels: {len(self.num_vessels)}')
        print(f'no. errors: {len(self.errors)}')

    def set_emailuser(self, username, email, address, phone_mobile, phone_home):
        items = address.split(',')
        line1 = ', '.join(items[:-2]).strip()
        state = items[-2].strip()
        postcode = items[-1].strip()

        firstname = username.split(' ')[-1].strip()
        lastname = ' '.join(username.split(' ')[:-1])

        try:
            user = EmailUser.objects.get(email=email)
        except:
            user = EmailUser.objects.create(email=email, first_name=firstname, last_name=lastname, mobile_number=phone_mobile, phone_number=phone_home)

        country = Country.objects.get(printable_name='Australia')
        try:
            _address = Address.objects.get(user=user)
            _address.line1 = line1
            _address.state = state
            _address.postcode = postcode
            _address.country = country
            _address.save()
        except:
            _address, address_created = Address.objects.get_or_create(line1=line1, state=state, postcode=postcode, country=country, user=user)
        user.residential_address = _address
        user.postal_address = _address
        user.save()
        self.emailuser.append(f'{email}')

        return user



    def get_vessel_details(self, idx, pers_no, username, rego_no, record):
        try:
            #import ipdb; ipdb.set_trace()
            if record:
                if rego_no != '0':
                    dot_name = record['DoTRego1']
                    ves_length = record['RegLength1']
                    ves_draft = record['Draft1']

                    record_people_name = self.search('PersNo', pers_no, self.people_name)
                    ves_name = record_people_name['_3']
                    email = record_people_name['EMail']

                    print(idx, email)
                    #import ipdb; ipdb.set_trace()
                    self.vessels_found.append(f'{pers_no} - {username} - {rego_no}')
                else:
                    #print(idx, f'No Reg {rego_no} - {username}')
                    self.vessels_not_found.append(f'{pers_no} - {username} - {rego_no}')
                    #import ipdb; ipdb.set_trace()
            else:
                print(idx, f'No Vessel Details {pers_no} - {username}')
                self.vessel_details_not_found.append(f'{pers_no} - {username} - {rego_no}')

        except Excception as e:
            self.errors.append(f'{idx} {record}\n{e}')
            import ipdb; ipdb.set_trace()
            #print(e)



