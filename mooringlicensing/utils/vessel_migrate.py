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
        self.vessel_multiple = self.read_dict('Vessel___Multiple_Vessels.json') # vessel rego and name
        self.user_rego = self.read_dict('UserRego.json') # vessel length/draft - if not available in vessel_multiple
        self.user_mooring = self.read_dict('UserMooring.json') # vessel length/draft - if not available in vessel_multiple
        self.people_no = self.read_dict('PeopleNo.json')                        # address/phone details (if no vessel_multiple details)
        self.people_cur_mooring = self.read_dict('People___Current_Mooring.json')                        # address/phone details (if no vessel_multiple details)
        #self.people_email = self.read_dict('People___eMail.json')                        # address/phone details (if no vessel_multiple details)
        self.people_email = self.read_dict('Licencees___Surname.json')                        # address/phone details (if no vessel_multiple details)


        self._auth_users = [
            #... can be found in directory tests/test.json
        ]

        self.vessels_found = []
        self.vessels_not_found = []
        self.vessel_details_not_found = []
        self.emailuser = []
        self.errors = []

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
        keys = ['_6', '_7', '_8', '_9', '_10']
        _vessels = []
        for i in range(no_vessel):
            items = record[keys[i]].split('-')
            rego = items[0].strip()
            vessel_name = items[1].strip()
            _vessels.append((rego, vessel_name, 0.0, 0.0)) # rego/name/length/draft
        return _vessels

    def to_float(self, val):
        try:
            return float(val)
        except Exception as e:
            return 0.0


    def migrate(self):

        #submitter = EmailUser.objects.get(email='jawaid.mushtaq@dbca.wa.gov.au')
        expiry_date = datetime.date(2023,8,31)
        date_applied = '2021-08-31'

# Licencees___Mooring_No.json --> self.mooring_no
#{'_8': '1', '_7': 'Stark Bay', 'MooringNo': 'SB008', 'UserName': 'Bain Kevin', 'PersNo': '000477', '_9': 'L Au', 'NoVessel': '4', '_1': 'P O Box 168, NORTH FREMANTLE, WA, 6159', 'StickerLNo1': 'None'    , '_4': 'DW106 - REALITY', 'StickerLNo2': 'None', '_11': 'DK819 - NO NAME', 'StickerLNo3': 'None', '_12': 'None', 'StickerLNo4': 'None', '_13': 'EF824 - NO NAME', 'StickerLNo5': 'None', '_15': 'None'    }

# Vessel___Multiple_Vessels.json --> self.vessel_multiple
#{'_4': '1', '_3': 'Auth User', 'PersNo': '202384', '_11': 'L Au', 'NoVessel': '2', 'UserName': 'Pearce Jeremy', '_6': '5000 - LACIOTAT', '_7': 'EN480 - NO NAME', '_8': 'None', '_9': 'None', '_10': 'None'}

# Vessel___Multiple_Vessels.csv
#{'_4': '1', '_3': 'Auth User', 'PersNo': '000477', '_11': 'L Au', 'NoVessel': '4', 'UserName': 'Bain Kevin', '_6': 'DW106 - REALITY', '_7': 'DK819 - NO NAME', '_8': 'EZ315 - NO NAME', '_9': 'EF824 -     NO NAME', '_10': 'None'}

# PeopleNo.json --> self.people_no
#{'PersNo': '000036', 'UserName': 'Timms Kyle', '_8': 'L Au', 'NoVessel': '1', '_1': '47 Robertson Road, KARDINYA, WA, 6163', 'PhoneHome': '9337 6632', 'PhoneMobile': '0413 437 901', 'PhoneWork': 'None'}

#UserRego.csv:666: self.user_rego
#{'VesRego': '77144', 'MooringNo': 'CB002', '_1': 'Timms Kyle', '_5': '000036', '_6': 'RIA', 'VesLen': '12.25', 'VesDraft': '1.20', 'VesName': 'ARENA'}

#UserMooring.csv:78: self.user_mooring
#{'_4': '1', 'MooringNo': 'CB012', '_1': 'Pearce Gary', 'VesRego': 'EI520', 'VesName': 'CEE CEE', '_6': 'Lic', 'VesLen': '6.40', 'VesDraft': '0.20', 'FirstNameL': 'Gary', 'LastNameL': 'Pearce'}


#People___eMail.csv:78: self.people_email
#{'LastName': 'Abbott', '_7': 'William', 'PersNo': '207907', '_8': 'W', 'NoVessel': '1', '_9': '1', 'EMail': 'wabbinator@gmail.com', 'LicContactEmail': 'None'}

        with transaction.atomic():
            #for idx, record in enumerate(self.moorings[827:], 827):
            import ipdb; ipdb.set_trace()
            #for idx, record in enumerate(self.vessel_rego_current[:60], 0):
            #for idx, record in enumerate(self.vessel_rego_current, 0):
            #for idx, record in enumerate(self.mooring_no[:300], 0):
            for idx, record in enumerate(self.mooring_no[12:], 0):
                try:
                    mooring_no  = record['MooringNo']
                    username = record['UserName']
                    pers_no  = record['PersNo']
                    address = record['_1']
                    no_vessel = int(float(record['NoVessel']))

                    if no_vessel > 0:
                        #print(f'{idx} Vessel details found: {username} {pers_no} {mooring_no} {no_vessel}')          
                        record_ves_details = self.search('PersNo', pers_no, self.vessel_multiple)
                        if not record_ves_details:
                            #import ipdb; ipdb.set_trace()
                            record_user_mooring = self.search('MooringNo', mooring_no, self.user_mooring)
                            # 'VesRego': 'EI520', 'VesName': 'CEE CEE', '_6': 'Lic', 'VesLen': '6.40', 'VesDraft': '0.20'
                            if record_user_mooring:
                                vessels = [(
                                    record_user_mooring['VesRego'], 
                                    record_user_mooring['VesName'], 
                                    record_user_mooring['VesLen'],
                                    record_user_mooring['VesDraft']
                                )]
                            else:
                                #record_mooring_details = self.search('MooringNo', mooring_no, self.mooring_details)
                                #vessels = [(record_mooring_details['VesLength'], record_user_mooring['Draft'], record_user_mooring['VesLen'], record_user_mooring['VesDraft'])]
                                items = record['_4'].split('-')
                                rego = items[0].strip()
                                vessel_name = items[1].strip()
                                vessels = [(rego, vessel_name, 0.0, 0.0)] #rego/name/length/draft

                        else:

                            vessels = self.get_vessels(no_vessel, record_ves_details)
                        print(f'{idx} Vessel details found: {username} {pers_no} {mooring_no} {no_vessel} {vessels}')          
                
                    else:
                        #print(f'{idx} No vessel details found: {username} {pers_no} {mooring_no} {no_vessel}')          
                        vessels = self.get_vessels(no_vessel, record_ves_details)
                        self.vessels_not_found.append(f'{idx} No vessel details found: {username} {pers_no} {mooring_no} {no_vessel} {vessels}')
                        #import ipdb; ipdb.set_trace()
                        record_people_no = self.search('PersNo', pers_no, self.people_no)

                    #import ipdb; ipdb.set_trace()
                    record_people_no = self.search('PersNo', pers_no, self.people_cur_mooring)
                    address = record_people_no['_1']
                    phone_home = record_people_no['PhoneHome']
                    phone_mobile = record_people_no['PhoneMobile']
                    phone_work = record_people_no['PhoneWork']

                    {'LastName': 'Abbott', '_7': 'William', 'PersNo': '207907', '_8': 'W', 'NoVessel': '1', '_9': '1', 'EMail': 'wabbinator@gmail.com', 'LicContactEmail': 'None'}
                    record_people_email = self.search('PersNo', pers_no, self.people_email)
                    email = record_people_email['EMail'].split(';')[0].strip().lower()

                    user = self.set_emailuser(username, email, address, phone_mobile, phone_home)

                    for ves in vessels:
                        try:
                            vessel = Vessel.objects.get(rego_no=ves[0])
                        except ObjectDoesNotExist:
                            vessel = Vessel.objects.create(rego_no=ves[0])

                        try:
                            owner = Owner.objects.get(emailuser=user)
                        except ObjectDoesNotExist:
                            owner = Owner.objects.create(emailuser=user)

                        try:
                            vessel_ownership = VesselOwnership.objects.get(owner=owner, vessel=vessel)
                            vessel_ownership.dot_name = '' #dot_name
                            vessel_ownership.save()
                        except ObjectDoesNotExist:
                            #vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=percentage, dot_name=dot_name)
                            vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=None, dot_name='')

                        if VesselDetails.objects.filter(vessel=vessel).count()>0:
                            vessel_details = VesselDetails.objects.filter(vessel=vessel)[0]
                        else:
                            vessel_details = VesselDetails.objects.create(
                                vessel_type='', #vessel_type,
                                vessel=vessel,
                                vessel_name=ves[1],
                                vessel_length=self.to_float(ves[2]),
                                vessel_draft=self.to_float(ves[3]),
                                #vessel_weight= vessel_weight,
                                #berth_mooring=berth_mooring
                            )


                except Exception as e:
                    self.errors.append(f'{idx} {record}\n{e}')
                    import ipdb; ipdb.set_trace()
                    print(e)

        print(f'vessels_found: {self.vessels_found}')
        print(f'vessels_not_found: {self.vessels_not_found}')
        print(f'vessel_details_not_found: {self.vessel_details_not_found}')
        print(f'errors: {self.errors}')
        print(f'no. vessels_found: {len(self.vessels_found)}')
        print(f'no. vessels_not_found: {len(self.vessels_not_found)}')
        print(f'no. vessel_details_not_found: {len(self.vessel_details_not_found)}')
        print(f'no. emailuser: {len(self.emailuser)}')
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


    def _migrate(self):

        #submitter = EmailUser.objects.get(email='jawaid.mushtaq@dbca.wa.gov.au')
        expiry_date = datetime.date(2023,8,31)
        date_applied = '2021-08-31'

        address_not_found = []
        address_l_not_found = []
        address_list = []
        user_list = []
        vessel_list = []
        owner_list = []
        ownership_list = []
        details_list = []
        proposal_list = []
        aup_list = []
        user_action_list = []
        approval_list = []
        approval_history_list = []

        added = []
        errors = []
        no_records = []
        fnames = []
        no_persno = []
        no_email = []
        no_email_l = []
        no_licencee = []
        count_no_mooring = 0
        with transaction.atomic():
            #for idx, record in enumerate(self.moorings[827:], 827):
            for idx, record in enumerate(self.moorings, 1):
                try:
                    #import ipdb; ipdb.set_trace()
                    username = record.get('_1') #.lower()
                    permit_type = record['_6'] # RIA or Lic
                    mooring_no  = record['MooringNo']
                    vessel_name = record['VesName']
                    #vessel_len  = aup_records[0]['VesLen']
                    rego_no = record['VesRego']

                    gs2 = GrepSearch2(username=username, mooring_no=mooring_no, path=self.path_csv)
                    try:
                        pers_no = gs2.get_persno()
                        if not pers_no and (username, pers_no) not in no_persno:
                            no_persno.append((username, pers_no))
                            print(f'** NO PersNo FOUND: {idx}, {pers_no}, {username}, {permit_type}, {mooring_no}')
                            continue
                    except:
                        if (username, pers_no) not in no_persno:
                            no_persno.append((username, pers_no))
                            print(f'NO PersNo FOUND: {idx}, {pers_no}, {username}, {permit_type}, {mooring_no}')
                        import ipdb; ipdb.set_trace()
                        continue

#                    if (username, pers_no) not in no_email:
#                        no_email.append((username,pers_no))
#                        print(f'NO EMAIL FOUND: {idx}, {pers_no}, {username}, {permit_type}, {mooring_no}')

                    address, phone_home, phone_mobile, phone_work = gs2.get_address(pers_no)
                    if address is None:
                        address_not_found.append(pers_no)
                        print(f'ADDRESS NOT FOUND: {idx}, {pers_no}, {username} {permit_type}, {mooring_no}')
                        continue
                    email, username = gs2.get_email()
                    if not email:
                        continue
                    email = email.split(';')[0]
                    email = email.strip().replace('{','').replace('}','')
                    firstname = username.split(' ')[-1]
                    lastname = ' '.join(username.split(' ')[:-1])

#                    if (username, pers_no) not in no_email:
#                        no_email.append((username,pers_no))
#                        print(f'NO EMAIL FOUND: {idx}, {pers_no}, {username}, {permit_type}, {mooring_no}')

                    email_l, username_l = gs2.get_email(licencee=True)
                    if username == username_l:
                        print(f'{idx}, Licencee and AUP Same User: {username}, {mooring_no}')
                        continue

                    #if not address_l and (username, pers_no, mooring_no) not in no_licencee and permit_type=='Lic':
                    if not email_l and permit_type=='Lic':
                        if (username, pers_no, mooring_no) not in no_licencee:
                            no_licencee.append((username, pers_no, mooring_no))
                        permit_type = 'RIA' # override and save as RIA nominated mooring
                        print(f'{idx}, {pers_no}, {address}, {username}, {permit_type}, {mooring_no}')
                    elif permit_type=='Lic':
                        email_l = email_l.split(';')[0]
                        firstname_l = username.split(' ')[-1]
                        lastname_l = ' '.join(username.split(' ')[:-1])
                        pers_no_l = gs2.get_persno(username_l)
                        #import ipdb; ipdb.set_trace()
                        address_l, phone_home_l, phone_mobile_l, phone_work_l = gs2.get_address(pers_no_l)
                        print(f'{idx}, {pers_no}, {address}, {username}, {permit_type}, {mooring_no}: Licencee - ({email_l} {username_l} {address_l}, {phone_mobile})')
                        if address_l is None:
                            address_l_not_found.append(pers_no_l)
                            print(f'ADDRESS_L NOT FOUND: {idx}, {pers_no}, {username}, {permit_type}, {mooring_no}: Licencee - ({pers_no_l})')
                            continue
                    else:
                        print(f'{idx}, {pers_no}, {address}, {username}, {permit_type}, {mooring_no}')



                    vessel_overall_length, vessel_draft = gs2.get_vessel_size(rego_no)
                    vessel_type = 'other'
                    vessel_weight = Decimal( 0.0 )
                    berth_mooring = ''
                    percentage = None # force user to set at renewal time
                    dot_name = gs2.get_dot_rego(rego_no)

                    if self.test:
                        #import ipdb; ipdb.set_trace()
                        continue
     
                    if Mooring.objects.filter(name=mooring_no).count()>0:
                        mooring = Mooring.objects.filter(name=mooring_no)[0]
                    elif mooring_no=='TB999':
                        print(f'{idx}, Mooring ignored: {mooring_no}')
                        continue
                    else:
                        import ipdb; ipdb.set_trace()
                        print(f'Mooring not found: {mooring_no}')
                        #mooring_bay = MooringBay.objects.get(name='Rottnest Island')
                        #mooring_bay = MooringBay.objects.get(name='Thomson Bay')

                    # User email user
                    items = address.split(',')
                    line1 = items[0].strip()
                    line2 = items[1].strip() if len(items) > 3 else ''
                    line3 = items[2].strip() if len(items) > 4 else ''
                    state = items[-2].strip()
                    postcode = items[-1].strip()

                    try:
                        user = EmailUser.objects.get(email=email)
                    except:
                        user = EmailUser.objects.create(email=email, first_name=firstname, last_name=lastname, mobile_number=phone_mobile, phone_number=phone_home)

                    country = Country.objects.get(printable_name='Australia')
                    try:
                        _address = Address.objects.get(user=user)
                    except:
                        _address, address_created = Address.objects.get_or_create(line1=line1, line2=line2, line3=line3, postcode=postcode, state=state, country=country, user=user)
                    user.residential_address = _address
                    user.postal_address = _address
                    user.save()

                    #if permit_type=='Lic' and email_l:
                    bay_preferences_numbered = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
                    mooring_authorisation_preference = 'ria'
                    site_licensee_email = None
                    keep_existing_mooring = True
                    site_licensee = False
                    if permit_type=='Lic':
                        # Licensee email usee
                        items = address_l.split(',')
                        line1 = items[0].strip()
                        line2 = items[1].strip() if len(items) > 3 else ''
                        line3 = items[2].strip() if len(items) > 4 else ''
                        state = items[-2].strip()
                        postcode = items[-1].strip()

                        #import ipdb; ipdb.set_trace()
                        try:
                            licensee = EmailUser.objects.get(email=email_l)
                        except:
                            licensee = EmailUser.objects.create(email=email_l, first_name=firstname_l, last_name=lastname_l, mobile_number=phone_mobile_l, phone_number=phone_home_l)

                        country = Country.objects.get(printable_name='Australia')
                        try:
                            _address_l = Address.objects.get(user=licensee)
                        except:
                            _address_l, address_created_l = Address.objects.get_or_create(line1=line1, line2=line2, line3=line3, postcode=postcode, state=state, country=country, user=licensee)
                        licensee.residential_address = _address_l
                        licensee.postal_address = _address_l
                        licensee.save()

                        mooring_authorisation_preference='site_licensee'
                        site_licensee_email=email_l
                        bay_preferences_numbered = None
                        site_licensee = True

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
                        vessel_ownership.dot_name = dot_name
                        vessel_ownership.save()
                    except ObjectDoesNotExist:
                        vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=percentage, dot_name=dot_name)

                    if VesselDetails.objects.filter(vessel=vessel).count()>0:
                        vessel_details = VesselDetails.objects.filter(vessel=vessel)[0]
                    else:
                        vessel_details = VesselDetails.objects.create(
                            vessel_type=vessel_type,
                            vessel=vessel,
                            vessel_name=vessel_name,
                            vessel_length=vessel_overall_length,
                            vessel_draft=vessel_draft,
                            vessel_weight= vessel_weight,
                            #berth_mooring=berth_mooring
                        )

                    proposal=AuthorisedUserApplication.objects.create(
                        proposal_type_id=1, # new application
                        submitter=user,
                        lodgement_date=datetime.now(),
                        mooring_authorisation_preference=mooring_authorisation_preference,
                        site_licensee_email=site_licensee_email,
                        keep_existing_mooring=True,
                        mooring=mooring,
                        bay_preferences_numbered=bay_preferences_numbered,
                        migrated=True,
                        vessel_details=vessel_details,
                        vessel_ownership=vessel_ownership,
                        rego_no=rego_no,
                        vessel_type=vessel_type,
                        vessel_name=vessel_name,
                        vessel_length=vessel_overall_length,
                        vessel_draft=vessel_draft,
                        #vessel_beam='',
                        vessel_weight=vessel_weight,
                        berth_mooring='home',
                        preferred_bay= mooring.mooring_bay,
                        percentage=percentage,
                        individual_owner=True,
                        dot_name=dot_name,
                        #proposed_issuance_approval={},
                        processing_status='approved',
                        customer_status='approved',
                        proposed_issuance_approval={
                            "details": None,
                            "cc_email": None,
                            "mooring_id": mooring.id,
                            "ria_mooring_name": mooring.name,
                            "mooring_bay_id": mooring.mooring_bay.id,
                            "vessel_ownership": [],
                            "mooring_on_approval": []
                        },
                    )
#>         "proposed_issuance_approval": {
#>             "details": "dd",
#>             "cc_email": null,
#>             "mooring_id": 127,
#>             "mooring_bay_id": 7,
#>             "ria_mooring_name": "CB005",
#>             "vesSEL_OWNERSHIP": [],
#>             "mooring_on_approval": []
#>         },
#
#>         "berth_mooring": "home",
#>         "dot_name": "abc",
#>         "insurance_choice": "over_ten",
#>         "preferred_bay": null,
#>         "silent_elector": null,
#>         "mooring_authorisation_preference": "ria",
#>         "bay_preferences_numbered": "[\"1\", \"2\", \"3\", \"4\", \"5\", \"6\", \"7\"]",

                    ua=ProposalUserAction.objects.create(
                        proposal=proposal,
                        who=user,
                        what='Authorised User Permit - Migrated Application',
                    )

                    try:
                        start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').date()
                    except:
                        start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d').date()

                    #approval = WaitingListAllocation.objects.create(
                    approval = AuthorisedUserPermit.objects.create(
                        status='current',
                        #internal_status=None,
                        current_proposal=proposal,
                        issue_date = datetime.datetime.now(datetime.timezone.utc),
                        #start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').date(),
                        start_date = start_date,
                        expiry_date = expiry_date,
                        submitter=user,
                        migrated=True,
                        export_to_mooring_booking=True,
                    )
                    #print(f'wla_order: {position_no}')

                    proposal.approval = approval
                    proposal.save()

                    moa = MooringOnApproval.objects.create(
                        approval=approval,
                        mooring=mooring,
                        sticker=None,
                        site_licensee=site_licensee,
                        #end_date=expiry_date
                    )

                    try:
                        start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').astimezone(datetime.timezone.utc)
                    except:
                        start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d').astimezone(datetime.timezone.utc)

                    approval_history = ApprovalHistory.objects.create(
                        reason='new',
                        approval=approval,
                        vessel_ownership = vessel_ownership,
                        proposal = proposal,
                        #start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d %H:%M:%S').astimezone(datetime.timezone.utc)
                        start_date = start_date,
                    )

                    added.append(proposal.id)

                    address_list.append(_address.id)
                    user_list.append(user.id)
                    vessel_list.append(vessel.id)
                    owner_list.append(owner.id)
                    ownership_list.append(vessel_ownership.id)
                    details_list.append(vessel_details.id)
                    proposal_list.append(proposal.proposal.id)
                    aup_list.append(proposal.id)
                    user_action_list.append(ua.id)
                    approval_list.append(approval.id)
                    approval_history_list.append(approval_history.id)

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
        print(f'AuthorisedUserApplication.objects.get(id__in={aup_list}).delete()')
#        print(f'ProposalUserAction.objects.get(id__in={user_action_list}).delete()')
        print(f'AuthorisedUserPermit.objects.get(id__in={approval_list}).delete()')
        print(f'ApprovalHistory.objects.get(id__in={approval_history_list}).delete()')
#        print(f'count_no_mooring: {count_no_mooring}')
        print(f'no_records: {no_records}')
        print(f'fnames_records: {fnames}')
        print(f'no_persno: {no_persno}')
        print(f'no_email: {no_email}')
        print(f'no_licencee: {no_licencee}')
        print(f'address_not_found: {address_not_found}')
        print(f'address_l_not_found: {address_l_not_found}')


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

            self.path + os.sep + 'Admin___EContacts___5_Licencee.json',
            self.path + os.sep + 'Admin___Labels___Postal.json',
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
        self.username = username.replace('  ', ' ')
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

        #import ipdb; ipdb.set_trace()
        try: 
            res = output.decode('utf-8')
            email = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['EMail']
            email = email.lower().strip('>').strip('<').strip()
        except:
            email = None

        #import ipdb; ipdb.set_trace()
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

    def get_vessel_size(self, rego_no):
        ''' Read all files in directory - Get PersNo'''
        #import ipdb; ipdb.set_trace()
        cmd = f"grep -ir '{rego_no}' {self.path} | grep RegLength1 | grep Draft1"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]

        try: 
            res = output.decode('utf-8')
            ves_length = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['RegLength1']
            ves_draft = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['Draft1']
            if ves_length == 'None':
                ves_length = 0.0
            if ves_draft == 'None':
                ves_draft = 0.0
        except:
            ves_length = 0.0
            ves_draft = 0.0

        return Decimal(ves_length), Decimal(ves_draft)

    def get_dot_rego(self, rego_no):
        ''' Read all files in directory - Get PersNo'''
        #import ipdb; ipdb.set_trace()
        cmd = f"grep -ir '{rego_no}' {self.path} | grep DoTRego1"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]

        try: 
            res = output.decode('utf-8')
            dot_rego = ast.literal_eval(res.splitlines()[0].split('csv:')[1])['DoTRego1']
        except:
            dot_rego = None

        return dot_rego


    def get_address(self, pers_no):
        ''' Read all files in directory - Get PersNo'''
        #import ipdb; ipdb.set_trace()
        cmd = f"grep -ir \"'PersNo': '{pers_no}'\" {self.path} | grep \"'_1'\" | grep UserName| grep Phone"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]

        try: 
#            res = output.decode('utf-8')
#            lines = res.splitlines()
#            for i in lines:
#                line = ast.literal_eval(lines[i].split('csv:')[1])
#                address = line['_1']
#                if len(address.split(',')) > 2:
#                    phone_home = line['PhoneHome']
#                    phone_mobile = line['PhoneMobile']
#                    phone_work = line['PhoneWork']
#                    break

            res = output.decode('utf-8')
            lines = res.splitlines()
            line = ast.literal_eval(lines[0].split('csv:')[1])
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

