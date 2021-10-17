import os
import subprocess
import json
import ast
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
    AuthorisedUserApplication,
    ProposalUserAction,
    Mooring,
    MooringBay,
)
from mooringlicensing.components.approvals.models import Approval, ApprovalHistory, MooringOnApproval, AuthorisedUserPermit


class AuthUserPermitMigration(object):
    '''
        from mooringlicensing.utils.waiting_list_migrate import WaitingListMigration, GrepSearch
        WaitingListMigration(test=False)
    '''

    #def __init__(self, path='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes', test=False):
    def __init__(self, path='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_07Oct2021', path_csv='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_all_csv', test=False):
        self.path = path
        self.path = path
        self.path_csv = path_csv
        self.test = test

        #self.waitlist = self.read_dict('Waitlist___Bay.json')
        self.auth_users_with_L = self.read_dict('Auth_Users___Surname___with_L.json')
        self.auth_users_No_L = self.read_dict('Auth_Users___Surname___No_L.json')
        self.moorings = self.read_dict('Auth_Users___Surname___Moorings.json')
        self.vessel_rego = self.read_dict('Auth_Users___Vessel_Rego.json')

        self.canc_lic = self.read_dict('Auth_Users___Cancelled_Lic.json')
        self.canc = self.read_dict('Auth_Users___Cancelled.json')


        self._auth_users = [
            #... can be found in directory tests/test.json
        ]

        self.migrate()

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

    def migrate(self):

        #submitter = EmailUser.objects.get(email='jawaid.mushtaq@dbca.wa.gov.au')
        expiry_date = datetime.date(2021,11,30)
        date_applied = '2020-08-31'

        address_list = []
        user_list = []
        vessel_list = []
        owner_list = []
        ownership_list = []
        details_list = []
        proposal_list = []
        wl_list = []
        user_action_list = []
        approval_list = []
        approval_history_list = []
        wla_list = []

        added = []
        errors = []
        no_records = []
        fnames = []
        no_persno = []
        no_email = []
        no_licencee = []
        count_no_mooring = 0
        with transaction.atomic():
            for idx, record in enumerate(self.moorings[:15], 1):
            #for idx, record in enumerate(self.moorings[11:13], 11):
            #for idx, record in enumerate(self.auth_users_No_L[33:200], 33):
            #for idx, record in enumerate(self.auth_users_No_L[46:], 46):
            #for idx, record in enumerate(self.auth_users_with_L, 1):
            #for idx, record in enumerate(self.auth_users_with_L[2:3], 1):
                try:
                    #import ipdb; ipdb.set_trace()
#                    no_auth_permits = int(record['NoAuth'])
#                    if no_auth_permits == 0:
#                        continue


                    #pers_no = record.get('PersNo')
                    #address = record.get('_1')
                    username = record.get('_1') #.lower()
                    permit_type = record['_6'] # RIA or Lic
                    mooring_no  = record['MooringNo']
                    vessel_name = record['VesName']
                    #vessel_len  = aup_records[0]['VesLen']
                    vessel_rego = record['VesRego']

                    #persno_record, fname0 = GrepSearch(vessel_rego, path=self.path).search('RegoMult', 'PersNo')
                    #gs2 = GrepSearch2(username=username, mooring_no=mooring_no, path='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_all_csv')
                    gs2 = GrepSearch2(username=username, mooring_no=mooring_no, path=self.path_csv)
                    try:
                        pers_no = gs2.get_persno()
                        #persno_record, fname0 = GrepSearch(username, path=self.path).search('UserName', 'PersNo')
                        #pers_no = persno_record.get('PersNo')
                        if not pers_no and (username, pers_no) not in no_persno:
                            no_persno.append((username, pers_no))
                            print(f'** NO PersNo FOUND: {idx}, {pers_no}, {username}, {permit_type}, {mooring_no}')
                            continue
                    except:
                        if (username, pers_no) not in no_persno:
                            no_persno.append((username, pers_no))
                            print(f'NO PersNo FOUND: {idx}, {pers_no}, {username}, {permit_type}, {mooring_no}')
                        continue

                    if (username, pers_no) not in no_email:
                        no_email.append((username,pers_no))
                        print(f'NO EMAIL FOUND: {idx}, {pers_no}, {username}, {permit_type}, {mooring_no}')

                    address, phone_home, phone_mobile, phone_work = gs2.get_address(pers_no)
                    email, username = gs2.get_email()
                    firstname = username.split(' ')[-1]
                    lastname = ' '.join(username.split(' ')[:-1])

                    if (username, pers_no) not in no_email:
                        no_email.append((username,pers_no))
                        print(f'NO EMAIL FOUND: {idx}, {pers_no}, {username}, {permit_type}, {mooring_no}')

                    #if fname0 not in fnames:
                    #    fnames.append(fname0)
                    #if fname1 not in fnames:
                    #    fnames.append(fname1)
                    #if fname2 not in fnames:
                    #    fnames.append(fname2)
                    #if fname3 not in fnames:
                    #    fnames.append(fname3)


                    email_l, username_l = gs2.get_email(licencee=True)
                    pers_no_l = gs2.get_persno(username_l)
                    address_l, phone_home_l, phone_mobile_l, phone_work_l = gs2.get_address(pers_no_l)
                    if not address_l and (username, pers_no, mooring_no) not in no_licencee and permit_type=='Lic':
                        no_licencee.append((username, pers_no, mooring_no))

                    #import ipdb; ipdb.set_trace()
                    print(f'{idx}, {pers_no}, {address}, {username}, {permit_type}, {mooring_no}: Licencee - ({email_l} {username_l} {address_l}, {phone_mobile})')

                    if self.test:
                        #import ipdb; ipdb.set_trace()
                        continue

 
                    ves_overall_length, ves_draft = gs2.get_vessel_size()
                    vessel_type = 'other'
                    vessel_weight = Decimal( 0.0 )
                    berth_mooring = ''

#                    mooring_record = self.search('_1', username, self.moorings)
#                    try:
#                        mooring = mooring_record['MooringNo']
#                        vessel_name = mooring_record['VesName']
#                        rego_no = mooring_record['VesRego']
#                    except:
#                        count_no_mooring += 1
#                        print(f'*************** {idx}, {pers_no}, {username}, {count_no_mooring}')
#                        continue
#                        #vessel_name = record.get('_11').split('-')[1].strip()
#                        #rego_no = record.get('_11').split('-')[0].strip()
#
                    #vessel_type = 'other'
                    #vessel_weight = Decimal( 0.0 )
                    #berth_mooring = record.get('_5')
                    #mooring = ?? # record.get('_5')
#
#                    # see mooringlicensing/utils/tests/mooring_names.txt
                    if Mooring.objects.filter(name=mooring_no).count()>0:
                        mooring = Mooring.objects.filter(name=mooring_no)[0]
                    else:
                        import ipdb; ipdb.set_trace()
                        print(f'Mooring not found: {mooring_no}')
                        #mooring_bay = MooringBay.objects.get(name='Rottnest Island')
                        #mooring_bay = MooringBay.objects.get(name='Thomson Bay')

                    percentage = None # force user to set at renewal time

                    items = address.split(',')
                    line1 = items[0].strip()
                    line2 = items[1].strip() if len(items) > 3 else ''
                    line3 = items[2].strip() if len(items) > 4 else ''
                    state = items[-2].strip()
                    postcode = items[-1].strip()
#
#                    #import ipdb; ipdb.set_trace()
#                    print(f'{idx}, {pers_no}, {username}, {state}, {postcode}')
#                    if self.test:
#                        continue
#
#                    try:
#                        user = EmailUser.objects.get(email=email)
#                    except:
#                        user = EmailUser.objects.create(email=email, first_name=firstname, last_name=lastname, mobile_number=mobile_no, phone_number=phone_no)
#
#                    country = Country.objects.get(printable_name='Australia')
#                    address, address_created = Address.objects.get_or_create(line1=line1, line2=line2, line3=line3, postcode=postcode, state=state, country=country, user=user)
#                    user.residential_address = address
#                    user.postal_address = address
#                    user.save()
#
#                    try:
#                        vessel = Vessel.objects.get(rego_no=rego_no)
#                    except ObjectDoesNotExist:
#                        vessel = Vessel.objects.create(rego_no=rego_no)
#
#
#                    try:
#                        owner = Owner.objects.get(emailuser=user)
#                    except ObjectDoesNotExist:
#                        owner = Owner.objects.create(emailuser=user)
#
#
#                    try:
#                        vessel_ownership = VesselOwnership.objects.get(owner=owner, vessel=vessel)
#                    except ObjectDoesNotExist:
#                        vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=percentage)
#
#                    try:
#                        vessel_details = VesselDetails.objects.get(vessel=vessel)
#                    except ObjectDoesNotExist:
#                        vessel_details = VesselDetails.objects.create(
#                        vessel_type=vessel_type,
#                        vessel=vessel,
#                        vessel_name=vessel_name,
#                        vessel_length=vessel_overall_length,
#                        vessel_draft=vessel_draft,
#                        vessel_weight= vessel_weight,
#                        #berth_mooring=berth_mooring
#                    )
#
#                    proposal=AuthorisedUserApplication.objects.create(
#                        proposal_type_id=1, # new application
#                        submitter=user,
#                        migrated=True,
#                        vessel_details=vessel_details,
#                        vessel_ownership=vessel_ownership,
#                        rego_no=rego_no,
#                        vessel_type=vessel_type,
#                        vessel_name=vessel_name,
#                        vessel_length=vessel_overall_length,
#                        vessel_draft=vessel_draft,
#                        #vessel_beam='',
#                        vessel_weight=vessel_weight,
#                        berth_mooring='home',
#                        preferred_bay= mooring.mooring_bay,
#                        percentage=percentage,
#                        individual_owner=True,
#                        #proposed_issuance_approval={},
#                        processing_status='approved',
#                        customer_status='approved',
#                        proposed_issuance_approval={
#                            "details": None,
#                            "cc_email": None,
#                            "mooring_id": mooring.id,
#                            "ria_mooring_name": mooring.name,
#                            "mooring_bay_id": mooring.mooring_bay.id,
#                            "vessel_ownership": [],
#                            "mooring_on_approval": []
#                        },
#                    )
##>         "proposed_issuance_approval": {
##>             "details": "dd",
##>             "cc_email": null,
##>             "mooring_id": 127,
##>             "mooring_bay_id": 7,
##>             "ria_mooring_name": "CB005",
##>             "vessel_ownership": [],
##>             "mooring_on_approval": []
##>         },
##
##>         "berth_mooring": "home",
##>         "dot_name": "abc",
##>         "insurance_choice": "over_ten",
##>         "preferred_bay": null,
##>         "silent_elector": null,
##>         "mooring_authorisation_preference": "ria",
##>         "bay_preferences_numbered": "[\"1\", \"2\", \"3\", \"4\", \"5\", \"6\", \"7\"]",
#
#                    ua=ProposalUserAction.objects.create(
#                        proposal=proposal,
#                        who=user,
#                        what='Authorised User Permit - Migrated Application',
#                    )
#
#                    try:
#                        start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').date()
#                    except:
#                        start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d').date()
#
#                    #approval = WaitingListAllocation.objects.create(
#                    approval = AuthorisedUserPermit.objects.create(
#                        status='current',
#                        #internal_status=None,
#                        current_proposal=proposal,
#                        issue_date = datetime.datetime.now(datetime.timezone.utc),
#                        #start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').date(),
#                        start_date = start_date,
#                        expiry_date = expiry_date,
#                        submitter=user,
#                        migrated=True,
#                        export_to_mooring_booking=True,
#                    )
#                    #print(f'wla_order: {position_no}')
#
#                    proposal.approval = approval
#                    proposal.save()
#
#                    moa = MooringOnApproval.objects.create(
#                        approval=approval,
#                        mooring=mooring,
#                        sticker=None,
#                        site_licensee=True, # ???
#                        end_date=expiry_date
#                    )
#
#                    try:
#                        start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').astimezone(datetime.timezone.utc)
#                    except:
#                        start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d').astimezone(datetime.timezone.utc)
#
#                    approval_history = ApprovalHistory.objects.create(
#                        reason='new',
#                        approval=approval,
#                        vessel_ownership = vessel_ownership,
#                        proposal = proposal,
#                        #start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').astimezone(datetime.timezone.utc)
#                        start_date = start_date,
#                    )
#
#                    added.append(proposal.id)
#
#                    address_list.append(address.id)
#                    user_list.append(user.id)
#                    vessel_list.append(vessel.id)
#                    owner_list.append(owner.id)
#                    ownership_list.append(vessel_ownership.id)
#                    details_list.append(vessel_details.id)
#                    proposal_list.append(proposal.proposal.id)
#                    wl_list.append(proposal.id)
#                    user_action_list.append(ua.id)
#                    approval_list.append(approval.id)
#                    approval_history_list.append(approval_history.id)

                except Exception as e:
                    #errors.append(str(e))
                    import ipdb; ipdb.set_trace()
                    raise Exception(str(e))

#        print(f'Address.objects.get(id__in={address_list}).delete()')
#        print(f'EmailUser.objects.get(id__in={user_list}).delete()')
#        print(f'Vessel.objects.get(id__in={vessel_list}).delete()')
#        print(f'Owner.objects.get(id__in={owner_list}).delete()')
#        print(f'VesselOwnership.objects.get(id__in={ownership_list}).delete()')
#        print(f'VesselDetails.objects.get(id__in={details_list}).delete()')
#        print(f'WaitingListApplication.objects.get(id__in={wl_list}).delete()')
#        print(f'ProposalUserAction.objects.get(id__in={user_action_list}).delete()')
#        print(f'WaitingListAllocation.objects.get(id__in={approval_list}).delete()')
#        print(f'ApprovalHistory.objects.get(id__in={approval_history_list}).delete()')
#        print(f'count_no_mooring: {count_no_mooring}')
        print(f'no_records: {no_records}')
        print(f'fnames_records: {fnames}')
        print(f'no_persno: {no_persno}')
        print(f'no_email: {no_email}')
        print(f'no_licencee: {no_licencee}')

def clear_record():
    Address.objects.last().delete()
    EmailUser.objects.last().delete()
    Vessel.objects.last().delete()
    Owner.objects.last().delete()
    VesselOwnership.objects.last().delete()
    VesselDetails.objects.last().delete()
    WaitingListApplication.objects.last().delete()
    ProposalUserAction.objects.last().delete()
    WaitingListAllocation.objects.last().delete()
    ApprovalHistory.objects.last().delete()

class GrepSearch(object):
    '''
    from mooringlicensing.utils.waiting_list_migrate import WaitingListMigration, GrepSearch

    GrepSearch('123').search('key', '_1')     --> Search for string key='123' in all files. The result record/dict must also have key '_1'
    '''

    #def __init__(self, search_str1, path='mooringlicensing/utils/lotus_notes'):
    def __init__(self, search_str1, path):
        self.path = path
        self.search_str1 = search_str1
        #self.search()

    def get_files(self, search_str):
        ''' Read all files in directory '''
        r=subprocess.check_output(['grep', '-rl', search_str, self.path])
        files = [i for i in r.decode('UTF-8').split('\n') if i.endswith(".json") ]
        return files

    def search(self, key1, key2):
        ''' Iteratively search for key:value pair in grep'd files '''

        def find(key, value, records):
            for record in records:
                if value in record.get(key):
                    return record
            return None

        #import ipdb; ipdb.set_trace()
        # Get all files that contains string 'self.search_str1'
        _files = self.get_files(self.search_str1)
        files=[

            self.path + os.sep + 'Auth_Users___Surname___with_L.json',
            self.path + os.sep + 'Auth_Users___Surname___No_L.json',
            self.path + os.sep + 'Vessel___People___All.json',
            self.path + os.sep + 'PeopleName.json',

            self.path + os.sep + 'Vessel___People___All.json',
            self.path + os.sep + 'Vessel___Rego___Current.json',
            self.path + os.sep + 'PeopleLicType.json',
            self.path + os.sep + 'People___Trim_File.json',
            self.path + os.sep + 'HINCurrent.json',
            self.path + os.sep + 'PeopleNo.json',
            self.path + os.sep + 'Vessel___Vessel_Name___Current.json',

#            self.path + os.sep + 'Vessel___Rego___Current.json',
#            self.path + os.sep + 'PeopleNo.json',
#            self.path + os.sep + 'People___Trim_File.json',
            self.path + os.sep + 'Admin___EContacts___5_Licencee.json',
            self.path + os.sep + 'Admin___Labels___Postal.json',
#
#            self.path + os.sep + 'Auth_User_Details.json',
#            self.path + os.sep + 'Auth_User___Inv.json',
#            self.path + os.sep + 'Auth_User_Payment_Summary.json',
#            self.path + os.sep + 'Auth_Users___AutoCanc.json',
#            self.path + os.sep + 'Auth_Users___Cancelled.json',
#            self.path + os.sep + 'Auth_Users___Cancelled_Lic.json',
#            self.path + os.sep + 'Auth_Users__Cancelled_Lic_Name.json',
#            self.path + os.sep + 'Auth_Users___Cancelled_PersNo.json',
#            self.path + os.sep + 'Auth_Users___Lic_Pers_No.json',
#            self.path + os.sep + 'Auth_Users___Mooring.json',
#            self.path + os.sep + 'Auth_Users___Sticker_No.json',
#            self.path + os.sep + 'Auth_Users___Surname___Moorings.json',
#            self.path + os.sep + 'Auth_Users___Surname___No.json',
#            self.path + os.sep + 'Auth_Users___Surname___No_L.json',
#            self.path + os.sep + 'Auth_Users___Surname___with_L.json',
#            self.path + os.sep + 'Auth_Users___User_Pers_No.json',
#            self.path + os.sep + 'Auth_Users___Vessel_Rego.json',
        ]

        for fname in files:
            with open(fname) as f:
                f_json = json.load(f)
                #import ipdb; ipdb.set_trace()
                # check the files (json) also has the key2
                if key2 in f_json[0]:
                    # find record in json that contains key1:search_str1
                    #import ipdb; ipdb.set_trace()
                    record = find(key1, self.search_str1, f_json)
                    if not record or (key2=='_1' and len(record['_1'].split(',')) <= 1):
                        continue
                    #print('****************' + fname)
                    return record, fname
        return None, None

class GrepSearch2(object):
    '''
    from mooringlicensing.utils.waiting_list_migrate import WaitingListMigration, GrepSearch

    GrepSearch('123').search('key', '_1')     --> Search for string key='123' in all files. The result record/dict must also have key '_1'
    '''

    def __init__(self, username, mooring_no, path):
        self.path = path
        self.username = username
        self.mooring_no = mooring_no

    def _get_result1(self):
        ''' Read all files in directory '''
        cmd = f"grep -r '{self.username}' {self.path} | grep \"'MooringNo': '{self.mooring_no}'\" | grep FirstNameL"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]

        try: 
            #import ipdb; ipdb.set_trace()
            res = output.decode('utf-8')
            firstname_l = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['FirstNameL']
            lastname_l = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['LastNameL']
            username_l = '{} {}'.format(lastname_l, firstname_l)
            return username_l

        except:
            return None

    def _get_result2(self):
        ''' Read all files in directory '''
        cmd = "grep -r '{self.username}' {self.path} | grep \"'MooringNo': '{self.mooring_no}'\" | grep '_12'"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]

        try: 
            #import ipdb; ipdb.set_trace()
            res = output.decode('utf-8')
            username_l = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['_12']
            return username_l

        except:
            return None


    def get_email(self, licencee=False):
        ''' Read all files in directory - Get Licensee email'''
        if licencee:
            username = self._get_result1()
            if not username:
                username = self._get_result2()
            #import ipdb; ipdb.set_trace()
            if not username:
                #import ipdb; ipdb.set_trace()
                return None, None
        else:
            username = self.username

        cmd = f"grep -r '{username}' {self.path} | grep '@'"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]

        try: 
            res = output.decode('utf-8')
            email = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['EMail']
        except:
            email = None

        return email, username

    def get_persno(self, username=None):
        ''' Read all files in directory - Get PersNo'''
        #import ipdb; ipdb.set_trace()
        #cmd = "grep -r '{}' {} | grep -v PersNoL | grep 'PersNo'".format(self.username, self.path)
        #cmd = "grep -ir '{}' {}/Auth_Users___*.* | grep -v PersNoL | grep 'PersNo'".format(self.username, self.path)
        if not username:
            username = self.username

        cmd = f"grep -ir '{username}' {self.path}/Auth_Users___*.* {self.path}/People___PersNo.csv {self.path}/People___Surname.csv | grep -v PersNoU | grep -v PersNoL | grep PersNo"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]

        try: 
            res = output.decode('utf-8')
            persno = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['PersNo']
            #persno = ast.literal_eval(res.splitlines()[0])['PersNo']
        except:
            persno = None

        return persno 

    def get_vessel_size(self):
        ''' Read all files in directory - Get PersNo'''
        #import ipdb; ipdb.set_trace()
        cmd = f"grep -ir '{self.vessel_rego}' {self.path} | grep RegLength1 | grep Draft1"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]

        try: 
            res = output.decode('utf-8')
            ves_length = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['RegLength1']
            ves_draft = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['Draft1']
        except:
            ves_length = None
            ves_draft = None

        return ves_length, ves_draft

    def get_address(self, pers_no):
        ''' Read all files in directory - Get PersNo'''
        #import ipdb; ipdb.set_trace()
        cmd = f"grep -ir \"'PersNo': '{pers_no}'\" {self.path} | grep \"'_1'\" | grep Phone"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]

        try: 
            res = output.decode('utf-8')
            line = ast.literal_eval(res.splitlines()[0].split('csv:')[1])
            address = line['_1']
            phone_home = line['PhoneHome']
            phone_mobile = line['PhoneMobile']
            phone_work = line['PhoneWork']
        except:
            address = None
            phone_home = None
            phone_mobile = None
            phone_work = None

        return address, phone_home, phone_mobile, phone_work

