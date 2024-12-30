from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
import time
import datetime
import pandas as pd
import numpy as np
from dateutil.parser import parse
from decimal import Decimal
from ledger_api_client.managed_models import SystemUser
from ledger_api_client.utils import get_or_create
from mooringlicensing.components.payments_ml.models import ApplicationFee, FeeCalculation, FeeItemApplicationFee, FeeItem, FeeSeason
from django.db.models import Q

from mooringlicensing.components.users.utils import (
    create_system_user, get_or_create_system_user, 
    get_user_name, get_or_create_system_user_address,
)

from mooringlicensing.components.proposals.models import (
    Proposal,
    ProposalApplicant,
    ProposalType,
    Vessel,
    Owner,
    VesselOwnership,
    VesselDetails,
    MooringLicenceApplication,
    AuthorisedUserApplication,
    WaitingListApplication,
    AnnualAdmissionApplication,
    ProposalUserAction,
    Mooring,
    MooringBay,
    ProposalSiteLicenseeMooringRequest,
)
from mooringlicensing.components.approvals.models import (
    Approval, 
    ApprovalHistory, 
    MooringLicence, 
    AuthorisedUserPermit,
    VesselOwnershipOnApproval, 
    MooringOnApproval,
    WaitingListAllocation,
    AnnualAdmissionPermit,
    ApprovalUserAction,
    Sticker,
    DcvOrganisation,
    DcvPermit,
    DcvVessel,
)

from tqdm import tqdm
import logging
logger = logging.getLogger(__name__)

NL = '\n'

TODAY = datetime.datetime.now(datetime.timezone.utc).date()
EXPIRY_DATE = datetime.date(2025,8,31)
START_DATE = datetime.date(2024,9,1)
DATE_APPLIED = '2024-09-01'
FEE_SEASON = '2024 - 2025'

VESSEL_TYPE_MAPPING = {
    'A': 'Catamaran',
    'B': 'Bow Rider',
    'C': 'Cabin Cruiser',
    'E': 'Centre Console',
    'F': 'Ferry',
    'G': 'Rigid Inflatable',
    'H': 'Half Cabin',
    'I': 'Inflatable',
    'L': 'Launch',
    'M': 'Motor Sailer',
    'O': 'Open Boat',
    'P': 'Power Boat',
    'R': 'Runabout',
    'S': 'Fishing Boat',
    'T': 'Tender',
    'W': 'Walkaround',
    'Y': 'Yacht',
}

USER_COLUMN_MAPPING = {
    'Person No':                        'pers_no',
    'Type of Licences':                 'licences_type', 
    'Cancelled':                        'cancelled', 
    'Paid Up?':                         'paid_up', 
    'BP$':                              'bp',
    'First Name':                       'first_name', 
    'Middle1 Initial':                  'middle_name', 
    'Last Name':                        'last_name', 
    'Age':                              'age', 
    'Date of Birth':                    'dob', 
    'Company':                          'company', 
    'Address':                          'address', 
    'Suburb':                           'suburb',
    'State':                            'state', 
    'Post Code':                        'postcode', 
    'Postal Address':                   'postal_address',
    'Postal Suburb':                    'postal_suburb', 
    'Postal State':                     'postal_state', 
    'Postal Post Code':                 'postal_postcode',
    'Electoral Roll':                   'electoral_role', 
    'Phone Home':                       'home_number', 
    'Phone Work':                       'work_number',
    'Phone Mobile':                     'mobile_number', 
    'Fax':                              'fax', 
    'e-Mail Address':                   'email',
    'Email Promotions':                 'email_prom', 
    'Waitlist Bay':                     'wl_bay', 
    'Bays Auth for':                    'bays_auth_for', 
    'No Bays Auth for':                 'no_bays_auth_for', 
    'Vessel Sold':                      'vessel_sold',
    'Current Mooring No':               'current_mooring_no', 
    'Vsl Due Date':                     'ves_due_date', 
    'No Users (for Lics)':              'no_user_lics',
}


ML_COLUMN_MAPPING = {
    'Mooring Number':                   'mooring_no', 
    'Licencee First Name':              'first_name_l',
    'Licencee Last Name':               'last_name_l',
    'Pers No':                          'pers_no',
    'Grandfather':                      'grandfather',
    'Tonnage':                          'tonnage',
    'Cert for addn Vessel':             'cert_addn_vessel',
    'Mooring Type':                     'mooring_type',
    'Float Colour':                     'float_colour',
    'Enviro Specs':                     'enviro_specs',
    'Buoy Specs':                       'buoy_specs',
    'Mooring Bay':                      'mooring_bay',
    'Cancelled':                        'cancelled',
    'No Auth Users  2012':              'no_auth_user_2012',
    'No Auth Users  2012 RIA':          'no_auth_users_2012_ria',
    'No Auth Users  2012 Lic':          'no_auth_user_2012_lic',
    'No Auth Users':                    'no_auth_users',
    'No Auth Users Lic':                'no_auth_user_lic',
    'No Auth Users XL':                 'no_auth_users_xl',
    'Colour Current':                   'colour',
    'Current Max Vessel on Site':       'max_vessel_on_site',
    'Lic Ves Length':                   'ves_length_lic',
    'Draft':                            'draft',
    'Max Ves Length':                   'max_ves_length',
    'Comments/Notes':                   'comments_notes',
    'Comments':                         'comments',
}

AU_COLUMN_MAPPING = {
    'Mooring Number':                   'mooring_no', 
    'Cancelled':                        'cancelled',
    'Licencee Approved Authorised User':'licencee_approved',
    'First Name (L)':                   'first_name_l',
    'Last Name (L)':                    'last_name_l',
    'Person No (L)':                    'pers_no_l',
    'User Type':                        'user_type',
    'Date Issued':                      'date_issued',
    'Sticker No':                       'sticker',
    'First Name (U)':                   'first_name_u',
    'Last Name (U)':                    'last_name_u',
    'Lic of Mooring No':                'lic_of_mooring_no',
    'PersNo (U)':                       'pers_no_u',
    'Vessel Rego':                      'vessel_rego',
    'Vessel Name':                      'vessel_name',
    'Vessel Length':                    'vessel_length',
    'Vessel Draft':                     'vessel_draft',
    'Date Cancelled':                   'date_cancelled',
    'Reason Cancelled':                 'reason_cancelled',
}

WL_COLUMN_MAPPING = {
    'FirstName':                        'first_name',
    'LastName':                         'last_name',
    'PersNo':                           'pers_no',
    'TrimNo':                           'trim_no',
    'Bay':                              'bay',
    'AppStatus':                        'app_status',
    'BayPosNo':                         'bay_pos_no',
    'SeqNo':                            'seq_no',
    'VesName':                          'vessel_name',
    'RegLength':                        'vessel_length',
    'VesRego':                          'vessel_rego',
    'Draft':                            'vessel_draft',
    'DateApplied':                      'date_applied',
    'DateCancelled':                    'date_cancelled',
    'DateAllocated':                    'date_allocated',
    'DateAnnConfRecd':                  'date_annconf_recd',
    'MooringNo':                        'mooring_no',
    'Cancelled':                        'cancelled',
    'Comment':                          'comment',
}


AA_COLUMN_MAPPING = {
    'ID':                               'id',
    'Date Created':                     'date_created',
    'First Name':                       'first_name',
    'Last Name':                        'last_name',
    'Postal Address 1':                 'address',
    'Suburb':                           'suburb',
    'State':                            'state',
    'Post Code':                        'postcode',
    'Sticker No':                       'sticker_no',
    'Vessel Rego':                      'rego_no',
    'Email':                            'email',
    'Mobile':                           'mobile_number',
    'Phone':                            'work_number',
    'Vessel Name':                      'vessel_name',
    'Vessel Length':                    'vessel_length',
    'Year':                             'year',
    'Status':                           'status',
    'Booking Period':                   'booking_period',
    'Country':                          'country',
}

class MooringLicenceReader():
    """
    First need to run clean().
    This will write output files to /var/www/mooringlicensing/mooringlicensing/utils/csv/clean
        from mooringlicensing.utils.export_clean import clean
        clean()
        
    Notes:
    Clean CSV
             1. open vessel_details in vi and replace the str chars --> ':%s/"//g'
             2. vessel_details - 'Person No' 210406 - has extra column delete cell B

    Manual Clean:
             3. For Mooring Booking, convert the downloaded file Moorings-RIA to pip-delimited (annual_admissions_booking_report.csv)
        
    FROM shell_plus:
        from mooringlicensing.utils.mooring_licence_migrate_pd import MooringLicenceReader
        mlr=MooringLicenceReader('PersonDets.txt', 'MooringDets.txt', 'VesselDets.txt', 'UserDets.txt', 'ApplicationDets.txt', 'annual_admissions_booking_report.csv')

        mlr.create_users()
        mlr.create_vessels()
        mlr.create_mooring_licences()
        mlr.create_authuser_permits()
        mlr.create_waiting_list()
        mlr.create_dcv()
        mlr.create_annual_admissions()

        mlr.create_pdf_ml()
        mlr.create_pdf_aup()
        mlr.create_pdf_wl()
        mlr.create_pdf_aa()
        mlr.create_pdf_dcv()

    OR
        from mooringlicensing.utils.mooring_licence_migrate_pd import MooringLicenceReader
        mlr=MooringLicenceReader('PersonDets.txt', 'MooringDets.txt', 'VesselDets.txt', 'UserDets.txt', 'ApplicationDets.txt', 'annual_admissions_booking_report.csv')
        mlr.run_migration

    FROM mgt-command:
        python manage_ml.py mooring_migration_script --filename mooringlicensing/utils/csv/MooringDets20221201-083202.txt


    Check for unique permit numbers
        pm = df['permit_number'].value_counts().loc[lambda x: x>1][1:].astype('int')
        pm.to_excel('/tmp/permit_numbers.xlsx')

    From RKS:

    from mooringlicensing.utils.mooring_licence_migrate_pd import MooringLicenceReader
    mlr=MooringLicenceReader('PersonDets.txt','MooringDets.txt','VesselDets.txt','UserDets.txt','ApplicationDets.txt','annual_admissions_booking_report.csv',path='/app/shared/clean/clean_22Dec2022/')

    CLEAR DB Records:
        MooringLicenceApplication.objects.all().delete()
        AuthorisedUserApplication.objects.all().delete()
        WaitingListApplication.objects.all().delete()
        DcvPermit.objects.all().delete()
        AnnualAdmissionApplication.objects.all().delete()
        Sticker.objects.all().delete()
        Approval.objects.all().delete()
        ApprovalHistory.objects.all().delete()
        Proposal.objects.all().delete()
        ProposalApplicant.objects.all().delete()
        Vessel.objects.all().delete()
        Owner.objects.all().delete()
        VesselOwnership.objects.all().delete()
        Mooring.objects.all().delete()
        MooringBay.objects.all().delete()

        !./manage_ml.py loaddata mooringlicensing/fixtures/mooring_mooring_bay.json

    """

    def __init__(self, fname_user, fname_ml, fname_ves, fname_authuser, fname_wl, fname_aa, path='/data/data/projects/mooringlicensing/tmp/clean/'):
        start_time = time.time()
        start_datetime = datetime.datetime.now()
        
        self.df_user=pd.read_csv(path+fname_user, delimiter='-!-', dtype=str)
        self.df_ml=pd.read_csv(path+fname_ml, delimiter='-!-', dtype=str)
        self.df_ves=pd.read_csv(path+fname_ves, delimiter='-!-', dtype=str)
        self.df_authuser=pd.read_csv(path+fname_authuser, delimiter='-!-', dtype=str)
        self.df_wl=pd.read_csv(path+fname_wl, delimiter='-!-', dtype=str)
        self.df_aa=pd.read_csv(path+fname_aa, delimiter=',', dtype=str)

        self.df_user=self._read_users()
        self.df_ml=self._read_ml()
        self.df_ves=self._read_ves()
        self.df_authuser=self._read_au()
        self.df_wl=self._read_wl()
        self.df_aa=self._read_aa()
        self.df_dcv=self._read_dcv()

        # create_users
        self.pers_ids = []
        self.user_created = []
        self.system_user_created = []
        self.user_existing = []
        self.system_user_existing = []
        self.user_errors = []
        self.no_email = []
        self.user_error_details = []

        # create_vessels
        self.vessels_created = []
        self.vessels_existing = []
        self.vessels_errors = []
        self.pct_interest_errors = []
        self.no_ves_rows = []

        # create_vessels
        self.ml_user_not_found = []
        self.ml_no_ves_rows = []

        #summary_file
        self.summary_file = path + "migration_summary_" + str(start_datetime).replace(" ", "_").replace(".", ":") + ".txt"
        end_time = time.time()

        #create summary file, add init time
        f = open(self.summary_file, "w")
        f.write("Mooring Licensing Migration Summary\n")
        f.write("\nInitialisation started at: {}".format(start_datetime))
        f.write("\nTime taken for initialisation: {}s".format(end_time-start_time))
        f.close()

    def __get_phone_number(self, row):
        if 'work_number' in row and row.work_number:
            row.work_number.replace(' ', '')
            return row.work_number

        elif 'home_number' in row and row.home_number:
            row.home_number.replace(' ', '')
            return row.home_number

    def __get_mobile_number(self, row):
        return row.mobile_number.replace(' ', '')

    def _read_users(self):
        # Rename the cols from Spreadsheet headers to Model fields names
        df_user = self.df_user.rename(columns=USER_COLUMN_MAPPING)
        df_user[df_user.columns] = df_user.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
 
        # clean everything else
        df_user.fillna('', inplace=True)
        df_user.replace({np.nan: ''}, inplace=True)

        return df_user

    def _read_ml(self):
        # Rename the cols from Spreadsheet headers to Model fields names
        df_ml = self.df_ml.rename(columns=ML_COLUMN_MAPPING)
        df_ml[df_ml.columns] = df_ml.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
 
        # clean everything else
        df_ml.fillna('', inplace=True)
        df_ml.replace({np.nan: ''}, inplace=True)

        # filter cancelled and rows with no name
        df_ml = df_ml[((df_ml['cancelled']!='Y')) & (df_ml['first_name_l'].isna()==False)]

        return df_ml

    def _read_ves(self):
        # clean everything else
        self.df_ves.fillna('', inplace=True)
        self.df_ves.replace({np.nan: ''}, inplace=True)

        return self.df_ves

    def _read_au(self):
        """ Read Auth User file """

        # Rename the cols from Spreadsheet headers to Model fields names
        df_authuser = self.df_authuser.rename(columns=AU_COLUMN_MAPPING)
        df_authuser[df_authuser.columns] = df_authuser.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
 
        # clean everything else
        df_authuser.fillna('', inplace=True)
        df_authuser.replace({np.nan: ''}, inplace=True)

        # filter cancelled
        df_authuser = df_authuser[(df_authuser['cancelled']!='Y')]

        return df_authuser

    def _read_wl(self):
        """ Read Auth User file """

        # Rename the cols from Spreadsheet headers to Model fields names
        df_wl = self.df_wl.rename(columns=WL_COLUMN_MAPPING)
        df_wl[df_wl.columns] = df_wl.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
        df_wl['bay_pos_no']= pd.to_numeric(df_wl['bay_pos_no'])
 
        # clean everything else
        df_wl.fillna('', inplace=True)
        df_wl.replace({np.nan: ''}, inplace=True)

        # filter cancelled and rows with no name
        df_wl = df_wl[(df_wl['app_status']=='W')]
        df_wl = df_wl.sort_values(['bay_pos_no'],ascending=True).groupby('bay').head(1000)

        return df_wl

    def _read_dcv(self):
        """ Read PersonDets file - for DCV Permits details """
        df_dcv = self.df_user[(self.df_user['company']!='') & (self.df_user['paid_up']=='Y') & (self.df_user['licences_type']=='C')]
        return df_dcv

    def _read_aa(self):
        """ Read Annual Admissions file created from 
            https://mooring-ria-internal.dbca.wa.gov.au/dashboard/bookings/annual-admissions/

            Eg. mooringlicensing/utils/csv/clean/annual_admissions_booking_report_20230125084027.csv
        """
        # Rename the cols from Spreadsheet headers to Model fields names
        df_aa = self.df_aa.rename(columns=AA_COLUMN_MAPPING)
        df_aa[df_aa.columns] = df_aa.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
 
        # clean everything else
        df_aa.fillna('', inplace=True)
        df_aa.replace({np.nan: ''}, inplace=True)

        # create dict of vessel details by rego_no
        logger.info('Creating Vessels details Dictionary ...')
        self.create_vessels_dict()

        return df_aa

    def run_migration(self):
        self.create_users()
        self.create_vessels()
        self.create_mooring_licences()
        self.create_authuser_permits()
        self.create_waiting_list()
        self.create_dcv()
        self.create_annual_admissions()
        self.create_licence_pdfs()

    def create_proposal_applicant(self, proposal, user, user_row):
        postal_same_as_res = user_row.address==user_row.postal_address or user_row.postal_address==''
        
        try:
            system_user = SystemUser.objects.get(ledger_id=user)
            names = get_user_name(system_user)
            if not system_user.legal_dob:
                dob = parse(user_row.dob).date() if user_row.dob else None
            else:
                dob = system_user.legal_dob

            if not system_user.phone_number:
                phone = system_user.phone_number
            else:
                phone = self.__get_phone_number(user_row)

            if not system_user.mobile_number:
                mobile = system_user.mobile_number
            else:
                mobile = self.__get_mobile_number(user_row)
        except Exception as e:
            print("error getting system user:",e)
            system_user = None
            names = {"first_name": user.first_name, "last_name": user.last_name}
            dob = parse(user_row.dob).date() if user_row.dob else None
            phone = self.__get_phone_number(user_row)
            mobile = self.__get_mobile_number(user_row)

        proposal_applicant = ProposalApplicant.objects.create(
           proposal=proposal,
           first_name=names["first_name"],
           last_name=names["last_name"],
           dob=dob,

           residential_address_line1=user_row.address,
           residential_address_locality=user_row.suburb,
           residential_address_state=user_row.state,
           residential_address_postcode=user_row.postcode,

           postal_address_line1=user_row.postal_address if not postal_same_as_res else user_row.address,
           postal_address_locality=user_row.postal_suburb if not postal_same_as_res else user_row.suburb,
           postal_address_state=user_row.postal_state if not postal_same_as_res else user_row.state,
           postal_address_postcode=user_row.postal_postcode if not postal_same_as_res else user_row.postcode,

           phone_number=phone,
           mobile_number=mobile,

           email=user.email,
           email_user_id=user.id,
        )

        residential_address_dict, postal_address_dict, use_for_postal = self.create_system_user_address_dict(proposal_applicant)
        if system_user:
            get_or_create_system_user_address(system_user,residential_address_dict)
            if use_for_postal:
                get_or_create_system_user_address(system_user,postal_address_dict,use_for_postal)

        return proposal_applicant

    def create_proposal_applicant_aa(self, proposal, user, user_row):

        try:
            system_user = SystemUser.objects.get(ledger_id=user)
            names = get_user_name(system_user)
            if not system_user.legal_dob:
                dob = parse(user.dob).date() if user.dob else None
            else:
                dob = system_user.legal_dob

            if not system_user.phone_number:
                phone = system_user.phone_number
            else:
                phone = self.__get_phone_number(user_row)

            if not system_user.mobile_number:
                mobile = system_user.mobile_number
            else:
                mobile = self.__get_mobile_number(user_row)
        except Exception as e:
            print("error getting system user:",e)
            system_user = None
            names = {"first_name": user.first_name, "last_name": user.last_name}
            dob = parse(user.dob).date() if user.dob else None
            phone = self.__get_phone_number(user_row)
            mobile = self.__get_mobile_number(user_row)

        proposal_applicant = ProposalApplicant.objects.create(
           proposal=proposal,
           first_name=names["first_name"],
           last_name=names["last_name"],
           dob=dob,

           residential_address_line1=user_row.address,
           residential_address_locality=user_row.suburb,
           residential_address_state=user_row.state,
           residential_address_postcode=user_row.postcode,

           postal_address_line1=user_row.address,
           postal_address_locality=user_row.suburb,
           postal_address_state=user_row.state,
           postal_address_postcode=user_row.postcode,

           phone_number=phone,
           mobile_number=mobile,

           email=user.email,
           email_user_id=user.id,
        )

        residential_address_dict, postal_address_dict, use_for_postal = self.create_system_user_address_dict(proposal_applicant)
        if system_user:
            get_or_create_system_user_address(system_user,residential_address_dict)
            if use_for_postal:
                get_or_create_system_user_address(system_user,postal_address_dict)

        return proposal_applicant

    def create_system_user_address_dict(self, applicant):
        residential_address_dict = {
            "line1": applicant.residential_address_line1,
            "locality": applicant.residential_address_locality,
            "state": applicant.residential_address_state,
            "postcode": applicant.residential_address_postcode,
            "country": 'AU',
            "address_type":"residential_address",
        }

        use_for_postal = (
            applicant.postal_address_line1==applicant.residential_address_line1 and
            applicant.postal_address_locality==applicant.residential_address_locality and
            applicant.postal_address_state==applicant.residential_address_state and
            applicant.postal_address_postcode==applicant.residential_address_postcode
        )
            
        postal_address_dict = {
            "line1": applicant.postal_address_line1,
            "locality": applicant.postal_address_locality,
            "state": applicant.postal_address_state,
            "postcode": applicant.postal_address_postcode,
            "country": 'AU',
            "address_type":"postal_address",
        }

        return residential_address_dict, postal_address_dict, use_for_postal

    def create_users(self):

        start_time = time.time()

        logger.info('Creating DCV users ...')
        df = self.df_dcv.groupby('pers_no').first()
        self._create_users_df(df)
        self.pers_ids_dcv = self.pers_ids

        logger.info('Creating ML & AU users ...')
        for pers_type in ['pers_no_u', 'pers_no_l']:
            df = self.df_authuser.groupby(pers_type).first()
            self._create_users_df(df)

        logger.info('Creating WL users ...')
        df = self.df_wl.groupby('pers_no').first()
        self._create_users_df(df)

        logger.info('Creating AA users ...')
        self._create_users_df_aa(self.df_aa)

        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nMigrate Users Summary\n")
        f.write("Migrate Users started at: {}\n".format(start_time))

        f.write(f'\nusers created:  {len(self.user_created)}')
        f.write(f'\nusers existing: {len(self.user_existing)}')
        f.write(f'\nusers errors:   {len(self.user_errors)}')
        f.write(f'\nsystem users created:  {len(self.system_user_created)}')
        f.write(f'\nsystem users existing: {len(self.system_user_existing)}')
        f.write(f'\nno_email errors:   {len(self.no_email)}')
        f.write(f'\nusers errors:   {self.user_errors}')
        f.write(f'\nno_email errors:   {self.no_email}')

        if self.user_error_details:
            f.write('\n\nusers error details\n')
            for i in self.user_error_details:
                f.write("\n"+i)

        f.write("\n\nTime taken for migrating users: {}s".format(end_time-start_time))
        f.close()

    def _create_users_df(self, df):
        # Iterate through the dataframe and create non-existent users
        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            try:
                if not row.name :
                    continue

                user_row = self.df_user[self.df_user['pers_no']==row.name]
                if user_row.empty:
                    continue

                if len(user_row)>1:
                    temp_user_row = user_row[user_row['paid_up']=='Y']
                    if temp_user_row.empty:
                        user_row = user_row[:1]
                    elif len(temp_user_row)>1:
                        # if still greater than 1, take first
                        user_row = user_row[:1]
                    else:
                        user_row = temp_user_row

                user_row = user_row.squeeze() # convert to Pandas Series

                email = user_row.email.lower().replace(' ','')
                if not email:
                    self.no_email.append(user_row.pers_no)
                    continue

                first_name = user_row.first_name.lower().title().strip()
                last_name = user_row.last_name.lower().title().strip()

                try:
                    dob = parse(user_row.dob).date() if user_row.dob else None
                except:
                    dob = None

                resp = get_or_create(email)       
                
                user_id = None             
                if resp['status'] == 200:
                    user_id = resp['data']['emailuser_id']
                    if resp['data']['record_status'] == 'new' and email not in self.user_existing:
                        self.user_created.append(email)
                        #create system user
                        system_user = create_system_user(user_id, email, first_name, last_name, dob)
                        self.system_user_created.append(email)
                    elif resp['data']['record_status'] == 'existing' and email not in self.user_existing:
                        self.user_existing.append(email)
                        #get or create system user
                        if not dob:
                            dob = parse(resp['data']['dob']).date() if resp['data']['dob'] else None
                        try:
                            system_user, created = get_or_create_system_user(user_id, email, first_name, last_name, dob)
                        except Exception as e:
                            print(e)
                            if str(e) != "Ledger Email User not Active":
                                logger.error(f'User creation failed: {email}')
                                self.user_errors.append(user_row.email)
                                self.user_error_details.append(row.name + " - " + user_row.email + " : Ledger Response: " + str(resp) + " " + str(e))
                            continue

                        if created:
                            self.system_user_created.append(email)
                        else:
                            self.system_user_existing.append(email)
                else:
                    logger.error(f'User creation failed: {email}')
                    self.user_errors.append(user_row.email)
                    self.user_error_details.append(row.name + " - " + user_row.email + " : Ledger Response: " + str(resp))

                self.pers_ids.append((user_id, row.name))

            except Exception as e:
                self.user_error_details.append(str(row.name) + " - " + str(user_row.email) + " : "+str(e))
                self.user_errors.append(user_row.email)
                logger.error(f'user: {row.name}   *********** 1 *********** FAILED. {e}')

        print(f'users created:  {len(self.user_created)}')
        print(f'users existing: {len(self.user_existing)}')
        print(f'users errors:   {len(self.user_errors)}')
        print(f'system users created:  {len(self.system_user_created)}')
        print(f'system users existing: {len(self.system_user_existing)}')
        print(f'no_email errors:   {len(self.no_email)}')
        print(f'users errors:   {self.user_errors}')
        print(f'no_email errors:   {self.no_email}')
        for i in self.user_error_details:
            print(i)

    def _create_users_df_aa(self, df):
        """ Reads the annual_admissions file created from the Mooring Booking System """
        # Iterate through the dataframe and create non-existent users
        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            try:
                user_row = self.df_user[self.df_user['email']==row.email]
                if user_row.empty:
                    user_row = row.copy()
                else:
                    if len(user_row)>1:
                        # if still greater than 1, take first
                        user_row = user_row[:1]
                    user_row = user_row.squeeze() # convert to Pandas Series
                    
                email = user_row.email.lower().replace(' ','')
                if not email:
                    self.no_email.append(user_row.id)
                    self.user_errors.append(user_row.email)
                    self.user_error_details.append(str(row.name) + " - " + user_row.email+" : Ledger Response: " + str(resp))
                    continue

                first_name = user_row.first_name.lower().title().strip()
                last_name = user_row.last_name.lower().title().strip()
                try:
                    dob = parse(user_row.dob).date() if user_row.dob else None
                except:
                    dob = None

                resp = get_or_create(email)    

                user_id = None              
                if resp['status'] == 200:
                    user_id = resp['data']['emailuser_id']    
                    if resp['data']['record_status'] == 'new' and email not in self.user_existing:
                        self.user_created.append(email)
                        #create system user
                        system_user = create_system_user(user_id, email, first_name, last_name, dob)
                        self.system_user_created.append(email)
                    elif resp['data']['record_status'] == 'existing' and email not in self.user_existing:
                        self.user_existing.append(email)
                        #get or create system user
                        if not dob:
                            dob = parse(resp['data']['dob']).date() if resp['data']['dob'] else None
                        try:
                            system_user, created = get_or_create_system_user(user_id, email, first_name, last_name, dob)
                        except Exception as e:
                            print(e)
                            if str(e) != "Ledger Email User not Active":
                                logger.error(f'User creation failed: {email}')
                                self.user_errors.append(user_row.email)
                                self.user_error_details.append(str(row.name) + " - " + user_row.email+" : Ledger Response: " + str(resp) + " " + str(e))
                            continue
                        if created:
                            self.system_user_created.append(email)
                        else:
                            self.system_user_existing.append(email)
                else:
                    logger.error(f'User creation failed: {email}')
                    self.user_errors.append(user_row.email)
                    self.user_error_details.append(str(row.name) + " - " + user_row.email+" : Ledger Response: " + str(resp))
                
                self.pers_ids.append((user_id, row.name))

            except Exception as e:
                if hasattr(user_row, "email"):
                    self.user_error_details.append(str(row.name) + " - " + str(user_row.email) + " : "+str(e))
                    self.user_errors.append(user_row.email)
                else:
                    self.user_error_details.append(str(row.name)+" : "+str(e))

        print(f'users created:  {len(self.user_created)}')
        print(f'users existing: {len(self.user_existing)}')
        print(f'users errors:   {len(self.user_errors)}')
        print(f'system users created:  {len(self.system_user_created)}')
        print(f'system users existing: {len(self.system_user_existing)}')
        print(f'no_email errors:   {len(self.no_email)}')
        print(f'users errors:   {self.user_errors}')
        print(f'no_email errors:   {self.no_email}')
        for i in self.user_error_details:
            print(i)

    def create_vessels(self):
        start_time = time.time()
        self._create_vessels()
        self._create_vessels_wl()

        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nMigrate Vessels Summary\n")
        f.write("Migrate Vessels started at: {}\n".format(start_time))

        f.write(f'\nvessels created:  {len(self.vessels_created)}')
        f.write(f'\nvessels errors:   {self.vessels_errors}')
        f.write(f'\nvessels errors:   {len(self.vessels_errors)}')

        f.write("\n\nTime taken for migrating vessels: {}s".format(end_time-start_time))
        f.close()

    def _create_vessels(self):

        def _ves_fields(prefix, ves_row, pers_no):
            ''' 
            Returns the 7 fields for a given field type (ves_dets file allows upto 7 vessels per pers_no/owner)
                Eg.
                    ves_fields('DoT Rego', ves_row, '000477')
                    Out[201]: ['GC1', 'DW106', 'DK819', 'EZ315', 'EF82']
            '''
            field1 = prefix + ' Nominated Ves'
            field2 = prefix + ' Ad Ves 2'
            field3 = prefix + ' Ad Ves 3'
            field4 = prefix + ' Ad Ves 4'
            field5 = prefix + ' Ad Ves 5'
            field6 = prefix + ' Ad Ves 6'
            field7 = prefix + ' Ad Ves 7'

          
            ves_list_raw = ves_row[[field1, field2, field3, field4, field5, field6, field7]].values.flatten().tolist()
            return [i[:-len(pers_no)] for i in ves_list_raw if i!=pers_no]  

        def ves_fields(ves_row):
            ves_details = []
            for colname_postfix in ['Nominated Ves', 'Ad Ves 2', 'Ad Ves 3', 'Ad Ves 4', 'Ad Ves 5', 'Ad Ves 6', 'Ad Ves 7']:
                cols = [col for col in ves_row.index if (colname_postfix in col)]
                ves_detail = ves_row[cols].to_dict()
                if ves_row['H. I. N. ' + colname_postfix] != '' or ves_row['DoT Rego ' + colname_postfix] != '':
                    ves_details.append(ves_detail)

            return ves_details

        def try_except(value):
            try:
                val = float(value)
            except Exception:
                val = 0.00
            return val

        self.vessels_au = {} 
        self.vessels_dcv = {} 
        postfix = ['Nominated Ves', 'Ad Ves 2', 'Ad Ves 3', 'Ad Ves 4', 'Ad Ves 5', 'Ad Ves 6', 'Ad Ves 7']
        for user_id, pers_no in tqdm(self.pers_ids):
            try:
                ves_rows = self.df_ves[self.df_ves['Person No']==pers_no]
                if len(ves_rows) > 1:
                    temp_ves_rows = ves_rows[(ves_rows['Au Sticker No Nominated Ves']!='')] #this checks if the vessel has an AU sticker
                    self.no_ves_rows.append((pers_no, len(temp_ves_rows)))
                    if len(temp_ves_rows) == 0:
                        ves_rows = ves_rows[0:]
                    else:
                        ves_rows = temp_ves_rows

                for idx, row in ves_rows.iterrows():
                    ves_row = row.to_frame()

                    ves_list = ves_fields(row)
                    try:
                        owner = Owner.objects.get(emailuser=user_id)
                    except ObjectDoesNotExist:
                        owner = Owner.objects.create(emailuser=user_id)

                    c_vessels = []
                    for i, ves in enumerate(ves_list):
                        ves_name=ves['Name ' + postfix[i]]
                        ves_type=ves['Type ' + postfix[i]]
                        rego_no=ves['DoT Rego ' + postfix[i]]
                        pct_interest=ves['%Interest ' + postfix[i]]
                        tot_length=ves['Reg Length ' + postfix[i]]
                        draft=ves['Draft ' + postfix[i]]
                        tonnage=ves['Tonnage ' + postfix[i]]
                        au_sticker=ves['Au Sticker No ' + postfix[i]]
                        c_sticker=ves['C Sticker No ' + postfix[i]]
                        au_sticker_date=ves['Date Au Sticker Sent ' + postfix[i]]

                        try:
                            ves_type = VESSEL_TYPE_MAPPING[ves_type]
                        except Exception as e:
                            ves_type = 'other'

                        try:
                            vessel = Vessel.objects.get(rego_no=rego_no)
                        except ObjectDoesNotExist:
                            vessel = Vessel.objects.create(rego_no=rego_no)

                        vessel_ownership = VesselOwnership.objects.filter(owner=owner, vessel=vessel).order_by("-created").first()
                        if not vessel_ownership:
                            pct_interest = int(round(float(try_except(pct_interest)),0))
                            
                            if pct_interest < 25:
                                self.pct_interest_errors.append((pers_no, rego_no, pct_interest))
                                pct_interest = 100
                            vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=pct_interest)

                        try:
                            vessel_details = VesselDetails.objects.get(vessel=vessel)
                            vessel_details.vessel_type = ves_type
                            vessel_details.save()
                        except MultipleObjectsReturned:
                            vessel_details = VesselDetails.objects.filter(vessel=vessel)[0]
                            vessel_details.vessel_type = ves_type
                            vessel_details.save()
                        except:
                            vessel_details = VesselDetails.objects.create(
                                vessel=vessel,
                                vessel_type=ves_type,
                                vessel_name=ves_name,
                                vessel_length=try_except(tot_length),
                                vessel_draft=try_except(draft),
                                vessel_weight=try_except(tonnage),
                                berth_mooring=''
                            )
                        self.vessels_au.update({rego_no: dict(au_sticker=au_sticker, au_sticker_sent=au_sticker_date)})
                        c_vessels.append((rego_no, c_sticker))

                    self.vessels_dcv.update({pers_no:c_vessels})
                    self.vessels_created.append((pers_no, len(c_vessels), c_vessels))

            except Exception as e:
                self.vessels_errors.append((pers_no, str(e)))
                continue

        print(f'vessels created:  {len(self.vessels_created)}')
        print(f'vessels errors:   {self.vessels_errors}')
        print(f'vessels errors:   {len(self.vessels_errors)}')
        print(f'vessels pct_int errors:   {self.pct_interest_errors}')
        print(f'vessels pct_int errors:   {len(self.pct_interest_errors)}')
        print(f'vessels no_ves_rows: {self.no_ves_rows}: Total len({self.no_ves_rows})')

    def _create_vessels_wl(self):

        def is_invalid_rego(element: any) -> bool:
            #If you expect None to be passed:
            if element is None:
                return True
            try:
                v = int(element)
                return v==0
            except ValueError:
                return False

        def try_except(value):
            try:
                val = float(value)
            except Exception:
                val = 0.00
            return val

        self.dummy_vessels = []
        df_wl = self.df_wl.groupby('vessel_rego').first()
        for index, row in tqdm(df_wl.iterrows(), total=df_wl.shape[0]):
            try:
                rego_no = row.name
                if is_invalid_rego(rego_no):
                    # User is on waiting list without a vessel - assign a dummy vessel
                    rego_no = f'{row.first_name}_{row.last_name}_{row.pers_no}'.lower()
                    self.dummy_vessels.append(rego_no)

                vessel, created = Vessel.objects.get_or_create(rego_no=rego_no)

                user_row = self.df_user[self.df_user['pers_no']==row.pers_no] 
                if user_row.empty:
                    continue

                if len(user_row)>1:
                    # if still greater than 1, take first
                    user_row = user_row[:1]
                user_row = user_row.squeeze() # convert to Pandas Series

                email = user_row.email.lower().replace(' ','')
                if not email:
                    self.no_email.append(user_row.pers_no)
                    continue

                users = EmailUser.objects.filter(email__iexact=email, is_active=True).order_by('-id')
                if users.count() == 0:
                    print(f'wl - email not found: {email}')
 
                    self.ml_user_not_found.append(email)
                    continue
                else:
                    user = users[0]
                    self.user_existing.append(email)


                try:
                    owner = Owner.objects.get(emailuser=user.id)
                except ObjectDoesNotExist:
                    owner = Owner.objects.create(emailuser=user.id)

                ves_type = 'other'
                vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=100)
                if rego_no in self.dummy_vessels:
                    vessel_ownership.end_date = TODAY

                try:
                    vessel_details = VesselDetails.objects.get(vessel=vessel)
                    vessel_details.vessel_type = ves_type
                    vessel_details.save()
                except MultipleObjectsReturned:
                    vessel_details = VesselDetails.objects.filter(vessel=vessel)[0]
                    vessel_details.vessel_type = ves_type
                    vessel_details.save()
                except:
                    vessel_details = VesselDetails.objects.create(
                        vessel=vessel,
                        vessel_type=ves_type,
                        vessel_name=row.vessel_name,
                        vessel_length=try_except(row.vessel_length),
                        vessel_draft=try_except(row.vessel_draft),
                        vessel_weight=try_except(0.0),
                        berth_mooring=''
                    )

            except Exception as e:
                self.vessels_errors.append((row.pers_no, str(e)))
                continue

        print(f'vessels created:  {len(self.vessels_created)}')
        print(f'vessels errors:   {self.vessels_errors}')
        print(f'vessels errors:   {len(self.vessels_errors)}')

    def create_vessels_dict(self):

        def ves_fields(ves_row):
            ves_details = []
            for colname_postfix in ['Nominated Ves', 'Ad Ves 2', 'Ad Ves 3', 'Ad Ves 4', 'Ad Ves 5', 'Ad Ves 6', 'Ad Ves 7']:
                cols = [col for col in ves_row.index if (colname_postfix in col)]

                ves_detail = ves_row[cols].to_dict()

                if ves_row['H. I. N. ' + colname_postfix] != '' or ves_row['DoT Rego ' + colname_postfix] != '':
                    ves_details.append(ves_detail)

            return ves_details

        self.vessels_dict = {} 
        postfix = ['Nominated Ves', 'Ad Ves 2', 'Ad Ves 3', 'Ad Ves 4', 'Ad Ves 5', 'Ad Ves 6', 'Ad Ves 7']
        for idx, row in tqdm(self.df_ves.iterrows(), total=self.df_ves.shape[0]):
            ves_row = row.to_frame()

            ves_list = ves_fields(row)

            au_vessels = {}
            c_vessels = []
            for i, ves in enumerate(ves_list):
                try:
                    ves_name=ves['Name ' + postfix[i]]
                    ves_type=ves['Type ' + postfix[i]]
                    rego_no=ves['DoT Rego ' + postfix[i]]
                    pct_interest=ves['%Interest ' + postfix[i]]
                    tot_length=ves['Reg Length ' + postfix[i]]
                    draft=ves['Draft ' + postfix[i]]
                    tonnage=ves['Tonnage ' + postfix[i]]
                    beam=ves['Beam ' + postfix[i]]
                    ml_sticker=ves['Lic Sticker Number ' + postfix[i]]
                    au_sticker=ves['Au Sticker No ' + postfix[i]]
                    c_sticker=ves['C Sticker No ' + postfix[i]]
                    au_sticker_date=ves['Date Au Sticker Sent ' + postfix[i]]

                    self.vessels_dict.update({rego_no:
                        {
                            'length':        tot_length,
                            'draft':         draft,
                            'beam':          beam,
                            'weight':        tonnage,
                            'name':          ves_name,
                            'type':          ves_type,
                            'percentage':    pct_interest,
                            'ml_sticker':    ml_sticker,
                            'au_sticker':    au_sticker,
                            'c_sticker':     c_sticker,
                            'au_sticker_date': au_sticker_date,
                        }
                    })

                except Exception as e:
                    print(f'ERROR: vessels_dict: {str(e)}')
                    if e.args[0]=='Name Ad Ves 2':
                        continue
                    


        print(f'vessels_dict dict size:  {len(self.vessels_dict)}')

    def create_mooring_licences(self):
        start_time = time.time()
        expiry_date = EXPIRY_DATE
        start_date = START_DATE
        date_applied = DATE_APPLIED
        mooring_not_found = []
        vessel_not_found = []
        owner_not_found = []
        vessel_ownership_not_found = []
        errors = []

        # Iterate through the ml dataframe and create MooringLicenceApplication's
        df = self.df_ml.groupby('mooring_no').first()
        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            try:
                if not row.name or len([_str for _str in ['KINGSTON REEF','NN64','PB 02','RIA'] if row.name in _str])>0:
                    continue

                user_row = self.df_user[self.df_user['pers_no']==row.pers_no] 

                if user_row.empty:
                    continue

                if len(user_row)>1:
                    user_row = user_row[(user_row['paid_up']=='Y')]

                if user_row.empty:
                    continue
                if len(user_row)>1:
                    # if still greater than 1, take first
                    user_row = user_row[:1]
                user_row = user_row.squeeze() # convert to Pandas Series

                email = user_row.email.lower().replace(' ','')
                if not email:
                    self.no_email.append(user_row.pers_no)
                    continue

                users = EmailUser.objects.filter(email__iexact=email, is_active=True).order_by('-id')
                if users.count() == 0:
                    print(f'ml - email not found: {email}')
 
                    self.ml_user_not_found.append(email)
                    continue
                else:
                    user = users[0]
                    self.user_existing.append(email)

                ves_row = self.df_ves[self.df_ves['Person No']==row.pers_no]
                if len(ves_row) > 1:
                    self.ml_no_ves_rows.append((user_row.pers_no, len(ves_row)))
                    ves_row = ves_row.iloc[0]
                else:
                    ves_row = ves_row.squeeze()

                postfix = 'Nominated Ves'
                ves_name = ves_row['Name ' + postfix]
                ves_type = ves_row['Type ' + postfix]
                rego_no = ves_row['DoT Rego ' + postfix]
                sticker_number = ves_row['Lic Sticker Number ' + postfix] 
                sticker_sent = ves_row['Licencee Sticker Sent ' + postfix] 
 
                ves_type = VESSEL_TYPE_MAPPING.get(ves_type, 'other')

                if ves_name=='':
                    continue 

                try:
                    owner = Owner.objects.get(emailuser=user.id)
                except Exception as e:
                    owner_not_found.append((row.pers_no, user, rego_no))
                    continue

                try:
                    vessel = Vessel.objects.get(rego_no=rego_no)
                except Exception as e:
                    vessel_not_found.append(rego_no)
                    continue

                vessel_ownership = VesselOwnership.objects.filter(owner=owner, vessel=vessel).order_by("-created").first()
                if not vessel_ownership:
                    vessel_ownership_not_found.append(rego_no)
                    continue
                
                try:
                    vessel_details = VesselDetails.objects.get(vessel=vessel)
                except MultipleObjectsReturned:
                    vessel_details = VesselDetails.objects.filter(vessel=vessel)[0]
                vessel_details.vessel_type = ves_type
                vessel_details.save()

                if Mooring.objects.filter(name=row.name).count()>0:
                    mooring = Mooring.objects.filter(name=row.name)[0]
                else:
                    mooring_not_found.append(row.name)
                    continue

                proposal=MooringLicenceApplication.objects.create(
                    proposal_type_id=ProposalType.objects.get(code='new').id, # new application
                    submitter=user.id,
                    lodgement_date=datetime.datetime.now().astimezone(), #TODO get actual
                    migrated=True,
                    vessel_details=vessel_details,
                    vessel_ownership=vessel_ownership,
                    rego_no=rego_no,
                    vessel_type=ves_type,
                    vessel_name=ves_name,
                    vessel_length=vessel_details.vessel_length,
                    vessel_draft=vessel_details.vessel_draft,
                    vessel_beam=vessel_details.vessel_beam,
                    vessel_weight=vessel_details.vessel_weight,
                    berth_mooring=vessel_details.berth_mooring,
                    preferred_bay= mooring.mooring_bay,
                    percentage=vessel_ownership.percentage,
                    individual_owner=True,
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
                        "vessel_ownership": [{
                                "id": vessel_ownership.id,
                                "dot_name": rego_no,
                                "checked": True
                            }],
                        "mooring_on_approval": []
                    },
                    date_invited=None, #TODO get actual?
                    dot_name=rego_no,
                )

                proposal_applicant = self.create_proposal_applicant(proposal, user, user_row)

                create_application_fee(proposal)

                ProposalUserAction.objects.create(
                    proposal=proposal,
                    who=user.id,
                    what='Mooring Site Licence - Migrated Application',
                )

                approval = MooringLicence.objects.create(
                    status='current',
                    current_proposal=proposal,
                    issue_date = datetime.datetime.now(datetime.timezone.utc),
                    start_date = start_date, #TODO get actual
                    expiry_date = expiry_date,
                    submitter=user.id,
                    migrated=True,
                    export_to_mooring_booking=True,
                )

                ApprovalUserAction.objects.create(
                    approval=approval,
                    who=user.id,
                    what='Mooring Site Licence - Migrated Application',
                )

                proposal.approval = approval
                proposal.save()
                alloc_mooring = proposal.allocated_mooring
                alloc_mooring.mooring_licence = approval
                alloc_mooring.save()

                vooa = VesselOwnershipOnApproval.objects.create(
                    approval=approval,
                    vessel_ownership=vessel_ownership,
                )

                start_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d').astimezone(datetime.timezone.utc)

                approval_history = ApprovalHistory.objects.create(
                    reason='new',
                    approval=approval,
                    vessel_ownership = vessel_ownership,
                    proposal = proposal,
                    start_date = start_date, #TODO get actual
                )

                try:
                    mailing_date = datetime.datetime.strptime(sticker_sent, '%d/%m/%Y').date() if sticker_sent else None
                except:
                    mailing_date = None

                if sticker_number:
                    sticker = Sticker.objects.create(
                        number=sticker_number,
                        status=Sticker.STICKER_STATUS_CURRENT,
                        approval=approval,
                        proposal_initiated=proposal,
                        vessel_ownership=vessel_ownership,
                        printing_date=None,
                        mailing_date=mailing_date,
                        sticker_printing_batch=None,
                        sticker_printing_response=None,
                        
                        postal_address_line1=proposal_applicant.postal_address_line1,
                        postal_address_locality=proposal_applicant.postal_address_locality,
                        postal_address_state=proposal_applicant.postal_address_state,
                        postal_address_country=proposal_applicant.postal_address_country,
                        postal_address_postcode=proposal_applicant.postal_address_postcode,
                    )

                    approval_history.stickers.add(sticker.id)

            except Exception as e:
                logger.error(f'ERROR: {row.name}. {str(e)}')
                self.user_errors.append(user_row.email)

        print(f'ml_user_not_found:  {self.ml_user_not_found}')
        print(f'Duplicate Pers_No in ves_row:  {self.ml_no_ves_rows}')
        print(f'ml_user_not_found:  {len(self.ml_user_not_found)}')
        print(f'Duplicate Pers_No in ves_row:  {len(self.ml_no_ves_rows)}')
        print(f'Moorings not Found:  {mooring_not_found}')
        print(f'Moorings not Found:  {len(mooring_not_found)}')
        print(f'Owners not Found:  {owner_not_found}')
        print(f'VesselOwnership not Found:  {len(vessel_ownership_not_found)}')
        print(f'VesselOwnership not Found:  {vessel_ownership_not_found}')
        print(f'Owners not Found:  {len(owner_not_found)}')
        print(f'Vessels not Found:  {vessel_not_found}')
        print(f'Vessels not Found:  {len(vessel_not_found)}')

        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nMigrate Mooring Licenses Summary\n")
        f.write("Migrate Mooring Licenses started at: {}\n".format(start_time))

        f.write(f'\nml_user_not_found:  {self.ml_user_not_found}')
        f.write(f'\nDuplicate Pers_No in ves_row:  {self.ml_no_ves_rows}')
        f.write(f'\nml_user_not_found:  {len(self.ml_user_not_found)}')
        f.write(f'\nDuplicate Pers_No in ves_row:  {len(self.ml_no_ves_rows)}')
        f.write(f'\nMoorings not Found:  {mooring_not_found}')
        f.write(f'\nMoorings not Found:  {len(mooring_not_found)}')
        f.write(f'\nOwners not Found:  {owner_not_found}')
        f.write(f'\nVesselOwnership not Found:  {len(vessel_ownership_not_found)}')
        f.write(f'\nVesselOwnership not Found:  {vessel_ownership_not_found}')
        f.write(f'\nOwners not Found:  {len(owner_not_found)}')
        f.write(f'\nVessels not Found:  {vessel_not_found}')
        f.write(f'\nVessels not Found:  {len(vessel_not_found)}')

        f.write("\n\nTime taken for migrating mooring licenses: {}s".format(end_time-start_time))
        f.close()

    def create_authuser_permits(self):
        start_time = time.time()
        expiry_date = EXPIRY_DATE
        start_date = START_DATE
        date_applied = DATE_APPLIED

        errors = []
        vessel_not_found = []
        aup_created = []
        au_stickers = []
        no_au_stickers = []

        bay_preferences_numbered = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
        vessel_type = 'other'

        df_authuser = self.df_authuser[(self.df_authuser['vessel_rego']!='0')].groupby('vessel_rego').first()
        for index, row in tqdm(df_authuser.iterrows(), total=df_authuser.shape[0]):
            try:
                user = None
                rego_no = row.name
                
                mooring_authorisation_preference = 'site_licensee' if row['licencee_approved']=='Y' else 'ria'
                mooring_qs = Mooring.objects.filter(name=row['mooring_no'])
                if mooring_qs.exists():
                    mooring = mooring_qs.first()
                else:
                    errors.append("Rego No " + str(rego_no) + ": Mooring with No. " + str(row['mooring_no']) + " does not exist") 
                    continue

                try:
                    email_l = self.df_user[(self.df_user['pers_no']==row['pers_no_l']) & (self.df_user['email']!='')].iloc[0]['email'].strip()
                except:
                    errors.append("Rego No " + str(rego_no) + ": User with Person No. " + str(row.pers_no_l) + " does not exist") 
                    continue
                
                try:
                    licensee = EmailUser.objects.filter(email__iexact=email_l.lower(), is_active=True).order_by('-id').first()
                except Exception as e:
                    errors.append("Rego No " + str(rego_no) + ": Licensee with email " + str(email_l.lower()) + " does not exist") 
                    continue

                if not (row['first_name_u']):
                    # This record represents Mooring Licence Holder - No need for an Auth User Permit
                    continue
                
                try:
                    email_u = self.df_user[(self.df_user['pers_no']==row.pers_no_u) & (self.df_user['email']!='')].iloc[0]['email'].strip()
                except:
                    errors.append("Rego No " + str(rego_no) + ": User with Person No. " + str(row.pers_no_u) + " does not exist") 
                    continue

                try:
                    user = EmailUser.objects.filter(email__iexact=email_u.lower(), is_active=True).order_by('-id').first()
                except Exception as e:
                    errors.append("Rego No " + str(rego_no) + ": User with email " + str(email_u.lower()) + " does not exist") 
                    continue

                rego_no = row.name
                sticker_info = self.vessels_au.get(rego_no)
                sticker_number = None
                if sticker_info:
                    sticker_number = sticker_info['au_sticker']
                    sticker_sent = sticker_info['au_sticker_sent']

                if sticker_number is None:
                    no_au_stickers.append(rego_no)
                else:
                    au_stickers.append(rego_no)

                
                try:
                    vessel = Vessel.objects.get(rego_no=rego_no)
                except Exception as e:
                    vessel_not_found.append(f'{row.pers_no_u} - {email_u}: {rego_no}')
                    continue

                if (vessel.vesselownership_set.exists()):
                    vessel_ownership = vessel.vesselownership_set.first()
                else:
                    errors.append("Rego No " + str(rego_no) + " - User Id " + str(user.id) + ": Vessel has no recorded ownership") 
                
                if (vessel.vesseldetails_set.exists()):
                    vessel_details = vessel.vesseldetails_set.first()
                else:
                    errors.append("Rego No " + str(rego_no) + " - User Id " + str(user.id) + ": Vessel has no recorded details") 

                proposal=AuthorisedUserApplication.objects.create(
                    proposal_type_id=ProposalType.objects.get(code='new').id, # new application
                    submitter=user.id,
                    lodgement_date=TODAY, #TODO get actual
                    mooring_authorisation_preference=mooring_authorisation_preference,
                    keep_existing_mooring=True,
                    bay_preferences_numbered=bay_preferences_numbered,
                    migrated=True,
                    vessel_details=vessel_details,
                    vessel_ownership=vessel_ownership,
                    rego_no=rego_no,
                    vessel_type=vessel_type,
                    vessel_name=row['vessel_name'],
                    vessel_length=vessel_details.vessel_length,
                    vessel_draft=vessel_details.vessel_draft,
                    vessel_beam=vessel_details.vessel_beam,
                    vessel_weight=vessel_details.vessel_weight,
                    berth_mooring=vessel_details.berth_mooring,
                    preferred_bay= mooring.mooring_bay,
                    percentage=vessel_ownership.percentage,
                    individual_owner=True,
                    dot_name=vessel_ownership.dot_name,
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

                #add site_licensee_mooring_request - we assume all migrated endorsements have been approved
                ProposalSiteLicenseeMooringRequest.objects.create(
                    proposal=proposal,
                    site_licensee_email=licensee.email,
                    mooring=mooring,
                    endorser_reminder_sent=True,
                    approved_by_endorser=True,
                )

                user_row = self.df_user[self.df_user['pers_no']==row.pers_no_u] 

                if user_row.empty:
                    continue

                if len(user_row)>1:
                    user_row = user_row[(user_row['paid_up']=='Y')]

                if user_row.empty:
                    continue
                if len(user_row)>1:
                    # if still greater than 1, take first
                    user_row = user_row[:1]

                user_row = user_row.squeeze() # convert to Pandas Series
                
                proposal_applicant=self.create_proposal_applicant(proposal, user, user_row)

                create_application_fee(proposal)

                ua=ProposalUserAction.objects.create(
                    proposal=proposal,
                    who=user.id,
                    what='Authorised User Permit - Migrated Application',
                )

                try:
                    issue_date = datetime.datetime.strptime(row['date_issued'].split(' ')[0], '%d/%m/%Y')
                except:
                    issue_date = start_date

                approval = AuthorisedUserPermit.objects.create(
                    status='current',
                    current_proposal=proposal,
                    issue_date = issue_date,
                    start_date = start_date, #TODO get actual
                    expiry_date = expiry_date,
                    submitter=user.id,
                    migrated=True,
                    export_to_mooring_booking=True,
                )

                proposal.approval = approval
                proposal.save()
                aup_created.append(approval.id)

                aua=ApprovalUserAction.objects.create(
                    approval=approval,
                    who=user.id,
                    what='Authorised User Permit - Migrated Application',
                )

                approval_history = ApprovalHistory.objects.create(
                    reason='new',
                    approval=approval,
                    vessel_ownership = vessel_ownership,
                    proposal = proposal,
                    start_date = start_date,
                )

                sticker = None
                if sticker_number:
                    sticker = Sticker.objects.create(
                        number=sticker_number,
                        status=Sticker.STICKER_STATUS_CURRENT, # 'current'
                        approval=approval,
                        proposal_initiated=proposal,
                        vessel_ownership=vessel_ownership,
                        printing_date=None, #TODAY,
                        mailing_date=datetime.datetime.strptime(sticker_sent, '%d/%m/%Y').date() if sticker_sent else None,
                        sticker_printing_batch=None,
                        sticker_printing_response=None,
                        
                        postal_address_line1=proposal_applicant.postal_address_line1,
                        postal_address_locality=proposal_applicant.postal_address_locality,
                        postal_address_state=proposal_applicant.postal_address_state,
                        postal_address_country=proposal_applicant.postal_address_country,
                        postal_address_postcode=proposal_applicant.postal_address_postcode,
                    )

                auth_user_moorings = self.df_authuser[(self.df_authuser['vessel_rego']==rego_no)].drop_duplicates(subset=['mooring_no','vessel_rego'])
                for idx, auth_user in auth_user_moorings.iterrows():
                    mooring = Mooring.objects.filter(name=auth_user.mooring_no)
                    moa = MooringOnApproval.objects.create(
                        approval=approval,
                        mooring=mooring[0],
                        sticker=sticker,
                        site_licensee=False,
                    )

            except Exception as e:
                print(e)
                if user:
                    errors.append("Rego No " + str(rego_no) + " - User Id " + str(user.id) + ":" + str(e))
                else:
                    errors.append("Rego No " + str(rego_no) + ":" + str(e))

        print(f'vessel_not_found: {vessel_not_found}')
        print(f'vessel_not_found: {len(vessel_not_found)}')
        print(f'aup_created: {len(aup_created)}')
        print(f'au_stickers: au_stickers, {len(au_stickers)}')
        print(f'no_au_stickers: no_au_stickers, {len(no_au_stickers)}')
        for i in errors:
            print(i)
        
        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nMigrate Authorised User Permits Summary\n")
        f.write("Migrate Authorised User Permits started at: {}\n".format(start_time))

        f.write(f'\nvessel_not_found: {vessel_not_found}')
        f.write(f'\nvessel_not_found: {len(vessel_not_found)}')
        f.write(f'\naup_created: {len(aup_created)}')
        f.write(f'\nau_stickers: au_stickers, {len(au_stickers)}')
        f.write(f'\nno_au_stickers: no_au_stickers, {len(no_au_stickers)}')
        if errors:
            f.write('\n\naup error details\n')
            for i in errors:
                f.write("\n"+i)

        f.write("\n\nTime taken for migrating authorised user permits: {}s".format(end_time-start_time))
        f.close()

    def create_waiting_list(self):
        start_time = time.time()
        expiry_date = EXPIRY_DATE
        start_date = START_DATE
        date_applied = DATE_APPLIED

        errors = []
        vessel_not_found = []
        user_not_found = []
        wl_created = []

        vessel_type = 'other'

        for index, row in tqdm(self.df_wl.iterrows(), total=self.df_wl.shape[0]):
            try:
                pers_no = row['pers_no']
                mooring_bay = MooringBay.objects.get(code=row['bay'])

                email = self.df_user[(self.df_user['pers_no']==pers_no) & (self.df_user['email']!='')].iloc[0]['email'].strip()
                first_name = row.first_name.lower().title().strip()
                last_name = row.last_name.lower().title().strip()
                try:
                    user = EmailUser.objects.filter(email__iexact=email.lower(), is_active=True).order_by('-id').first()
                except Exception as e:
                    errors.append("Rego No " + str(rego_no) + " - User Id " + str(user.id) + ": User with email " + str(email.lower()) + " does not exist") 
                    continue

                rego_no = row['vessel_rego']
                try:
                    vessel = Vessel.objects.get(rego_no=rego_no)
                except Exception as e:
                    vessel_not_found.append(f'{pers_no} - {email}: {rego_no}')
                    continue

                if (vessel.vesselownership_set.exists()):
                    vessel_ownership = vessel.vesselownership_set.first()
                else:
                    errors.append("Rego No " + str(rego_no) + " - User Id " + str(user.id) + ": Vessel has no recorded ownership") 
                
                if (vessel.vesseldetails_set.exists()):
                    vessel_details = vessel.vesseldetails_set.first()
                else:
                    errors.append("Rego No " + str(rego_no) + " - User Id " + str(user.id) + ": Vessel has no recorded details") 

                try:
                    lodgement_date = datetime.datetime.strptime(row.date_applied, '%d/%m/%Y').astimezone(datetime.timezone.utc)
                except:
                    lodgement_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d').astimezone(datetime.timezone.utc)

                proposal=WaitingListApplication.objects.create(
                    proposal_type_id=ProposalType.objects.get(code='new').id, # new application
                    submitter=user.id,
                    lodgement_date=lodgement_date,
                    migrated=True,
                    vessel_details=vessel_details,
                    vessel_ownership=vessel_ownership,
                    rego_no=rego_no,
                    vessel_type=vessel_type,

                    vessel_name=row['vessel_name'],
                    vessel_length=vessel_details.vessel_length,
                    vessel_draft=vessel_details.vessel_draft,
                    vessel_beam=vessel_details.vessel_beam,
                    vessel_weight=vessel_details.vessel_weight,
                    berth_mooring=vessel_details.berth_mooring,

                    preferred_bay=mooring_bay,
                    percentage=vessel_ownership.percentage,
                    individual_owner=True,
                    proposed_issuance_approval={},
                    processing_status='approved',
                    customer_status='approved',
                )

                user_row = self.df_user[self.df_user['pers_no']==row.pers_no]

                if user_row.empty:
                    continue

                if len(user_row)>1:
                    user_row = user_row[(user_row['paid_up']=='Y')]

                if user_row.empty:
                    continue
                if len(user_row)>1:
                    # if still greater than 1, take first
                    user_row = user_row[:1]

                user_row = user_row.squeeze() # convert to Pandas Series
                
                self.create_proposal_applicant(proposal, user, user_row)

                create_application_fee(proposal)

                ua=ProposalUserAction.objects.create(
                    proposal=proposal,
                    who=user.id,
                    what='Waiting List - Migrated Application',
                )

                try:
                    date_allocated = datetime.datetime.strptime(row['date_allocated'], '%d/%m/%Y').astimezone(datetime.timezone.utc)
                except Exception as e:
                    errors.append("date_allocated substituted with general start date: " + str(e))
                    date_allocated = start_date

                approval = WaitingListAllocation.objects.create(
                    status=Approval.APPROVAL_STATUS_CURRENT,
                    internal_status=Approval.INTERNAL_STATUS_WAITING,
                    current_proposal=proposal,
                    issue_date = date_allocated,
                    start_date = start_date, #TODO get actual
                    expiry_date = expiry_date,
                    submitter=user.id,
                    migrated=True,
                    wla_order=row['bay_pos_no'],
                    wla_queue_date=start_date + datetime.timedelta(seconds=int(row['bay_pos_no'])),
                )
                wl_created.append(approval.id)

                aua=ApprovalUserAction.objects.create(
                    approval=approval,
                    who=user.id,
                    what='Waiting List Allocation - Migrated Application',
                )

                proposal.approval = approval
                proposal.save()

                approval_history = ApprovalHistory.objects.create(
                    reason='new',
                    approval=approval,
                    vessel_ownership = vessel_ownership,
                    proposal = proposal,
                    start_date = start_date, #TODO get actual
                )

            except Exception as e:
                errors.append("Rego No " + str(rego_no) + " - User Id " + str(user.id) + ":" + str(e))

        print(f'vessel_not_found: {vessel_not_found}')
        print(f'vessel_not_found: {len(vessel_not_found)}')
        print(f'user_not_found: {user_not_found}')
        print(f'user_not_found: {len(user_not_found)}')
        print(f'wl_created: {len(wl_created)}')
        for i in errors:
            print(i)
        
        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nMigrate Waiting List Allocations Summary\n")
        f.write("Migrate Waiting List Allocations started at: {}\n".format(start_time))

        f.write(f'\nvessel_not_found: {vessel_not_found}')
        f.write(f'\nvessel_not_found: {len(vessel_not_found)}')
        f.write(f'\nuser_not_found: {user_not_found}')
        f.write(f'\nuser_not_found: {len(user_not_found)}')
        f.write(f'\nwl_created: {len(wl_created)}')
        if errors:
            f.write('\n\nwla error details\n')
            for i in errors:
                f.write("\n"+i)

        f.write("\n\nTime taken for migrating waiting list allocations: {}s".format(end_time-start_time))
        f.close()

    def create_dcv(self):
        start_time = time.time()
        expiry_date = EXPIRY_DATE
        start_date = START_DATE
        fee_season = FeeSeason.objects.filter(application_type__code='dcvp', name=FEE_SEASON)[0]

        errors = []
        vessel_not_found = []
        user_not_found = []
        dcv_created = []

        for index, row in tqdm(self.df_dcv.iterrows(), total=self.df_dcv.shape[0]):
            try:

                pers_no = row['pers_no']
                email = row['email']
                org_name = row['company']

                first_name = row.first_name.lower().title().strip()
                last_name = row.last_name.lower().title().strip()
                try:
                    user = EmailUser.objects.filter(email__iexact=email.lower(), is_active=True).order_by('-id').first()
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()
                except Exception as e:
                    errors.append("User Id " + str(user.id) + ": User with email " + str(email.lower()) + " does not exist") 
                    continue

                try:
                    dcv_organisation = DcvOrganisation.objects.get(name=org_name)
                except ObjectDoesNotExist:
                    dcv_organisation = DcvOrganisation.objects.create(name=org_name)

                try:
                    vessels_dcv = self.vessels_dcv[pers_no]
                except Exception as e:
                    vessel_not_found.append(pers_no)
                    continue

                user_row = self.df_user[self.df_user['pers_no']==row.pers_no]

                if user_row.empty:
                    continue

                if len(user_row)>1:
                    user_row = user_row[(user_row['paid_up']=='Y')]

                if user_row.empty:
                    continue
                if len(user_row)>1:
                    # if still greater than 1, take first
                    user_row = user_row[:1]

                user_row = user_row.squeeze() # convert to Pandas Series

                for rego_no, sticker_no in vessels_dcv:
                    try:
                        dcv_vessel = DcvVessel.objects.get(rego_no=rego_no)
                    except ObjectDoesNotExist:
                        vessel_details = VesselDetails.objects.get(vessel__rego_no=rego_no)
                        dcv_vessel = DcvVessel.objects.create(
                            rego_no = rego_no,
                            vessel_name = vessel_details.vessel_name,
                        )
                        dcv_vessel.dcv_organisations.add(dcv_organisation)

                    dcv_permit = DcvPermit.objects.create(
                        submitter = user.id,
                        applicant = user.id,
                        lodgement_datetime = datetime.datetime.now(datetime.timezone.utc), #TODO get actual
                        fee_season = fee_season,
                        start_date = start_date, #TODO get actual
                        end_date = expiry_date,
                        dcv_vessel = dcv_vessel,
                        dcv_organisation =dcv_organisation,
                        migrated = True,
                        postal_address_line1 = user_row.postal_address if user_row.postal_address else user_row.address,
                        postal_address_suburb = user_row.postal_suburb if user_row.postal_address else user_row.suburb,
                        postal_address_postcode = user_row.postal_postcode if user_row.postal_address else user_row.postcode,
                        postal_address_state = user_row.postal_state if user_row.postal_address else user_row.state,
                        postal_address_country = 'AU',
                        status=DcvPermit.DCV_PERMIT_STATUS_CURRENT,
                    )

                    if sticker_no:
                        sticker = Sticker.objects.create(
                            number=sticker_no,
                            status=Sticker.STICKER_STATUS_CURRENT, # 'current'
                            dcv_permit=dcv_permit,
                            mailing_date=TODAY,
                            
                            postal_address_line1=dcv_permit.postal_address_line1,
                            postal_address_locality=dcv_permit.postal_address_suburb,
                            postal_address_state=dcv_permit.postal_address_state,
                            postal_address_country=dcv_permit.postal_address_country,
                            postal_address_postcode=dcv_permit.postal_address_postcode,
                        )
                    dcv_created.append(dcv_permit.id)

            except Exception as e:
                errors.append("User Id " + str(user.id) + ": " + str(e)) 
                errors.append(str(e))

        print(f'vessel_not_found: {vessel_not_found}')
        print(f'vessel_not_found: {len(vessel_not_found)}')
        print(f'user_not_found: {user_not_found}')
        print(f'user_not_found: {len(user_not_found)}')
        print(f'dcv_created: {len(dcv_created)}')
        for i in errors:
            print(i)
        
        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nMigrate DCV Permits Summary\n")
        f.write("Migrate DCV Permits started at: {}\n".format(start_time))

        f.write(f'\nvessel_not_found: {vessel_not_found}')
        f.write(f'\nvessel_not_found: {len(vessel_not_found)}')
        f.write(f'\nuser_not_found: {user_not_found}')
        f.write(f'\nuser_not_found: {len(user_not_found)}')
        f.write(f'\ndcv_created: {len(dcv_created)}')
        if errors:
            f.write('\n\ndcv error details\n')
            for i in errors:
                f.write("\n"+i)

        f.write("\n\nTime taken for migrating dcv permits: {}s".format(end_time-start_time))
        f.close()

    def _create_single_vessel(self, user, rego_no, ves_name, ves_type, length, draft, beam, weight, pct_interest, berth_mooring=''):

        def try_except(value):
            try:
                val = float(value)
            except Exception:
                val = 0.00
            return val

        # check if vessel object exists
        try:
            vessel = Vessel.objects.get(rego_no=rego_no)
        except ObjectDoesNotExist:
            vessel = Vessel.objects.create(rego_no=rego_no)

        try:
            owner = Owner.objects.get(emailuser=user)
        except ObjectDoesNotExist:
            owner = Owner.objects.create(emailuser=user)

        vessel_ownership = VesselOwnership.objects.filter(owner=owner, vessel=vessel).order_by("-created").first()
        if not vessel_ownership:
            pct_interest = int(round(float(try_except(pct_interest)),0))
            if pct_interest < 25:
                pct_interest = 100
            vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=pct_interest)

        try:
            vessel_details = VesselDetails.objects.get(vessel=vessel)
        except MultipleObjectsReturned:
            vessel_details = VesselDetails.objects.filter(vessel=vessel)[0]
        except:
            vessel_details = VesselDetails.objects.create(
                vessel=vessel,
                vessel_type=ves_type,
                vessel_name=ves_name,
                vessel_length=try_except(length),
                vessel_draft=try_except(draft),
                vessel_weight=try_except(weight),
                vessel_beam=try_except(beam),
                berth_mooring=''
            )

        return vessel, vessel_details, vessel_ownership

    def create_annual_admissions(self):
        start_time = time.time()
        """
            mlr=MooringLicenceReader('PersonDets20221222-125823.txt', 'MooringDets20221222-125546.txt', 'VesselDets20221222-125823.txt', 'UserDets20221222-130353.txt', 'ApplicationDets20221222-125157.txt','annual_admissions_booking_report_20230125084027.csv')
            mlr.create_users()
            mlr.create_vessels()
            mlr.create_annual_admissions()
        """
        expiry_date = EXPIRY_DATE
        start_date = START_DATE
        date_applied = DATE_APPLIED

        errors = []
        vessel_details_not_found = []
        rego_aa_created = []
        total_aa_created = []

        vessel_type = 'other'

        for index, row in tqdm(self.df_aa.iterrows(), total=self.df_aa.shape[0]):
            try:
                rego_no = row['rego_no']
                email = row['email']
                sticker_no = row['sticker_no']
                date_created = row['date_created']
                vessel_name = row['vessel_name']
                vessel_length = row['vessel_length']

                try:
                    user = EmailUser.objects.filter(email__iexact=email.lower().strip(), is_active=True).order_by('-id').first()
                except Exception as e:
                    errors.append("User with email " + str(email.lower()) + " does not exist") 
                    continue

                vessel_dict = self.vessels_dict.get(rego_no)
                if vessel_dict is None:
                    vessel, vessel_details, vessel_ownership = self._create_single_vessel(
                        user.id, 
                        rego_no, 
                        ves_name=vessel_name, # use vessel_name from AA Moorings Spreasheet
                        ves_type=vessel_type,
                        length=vessel_length, # use vessel_length from AA Moorings Spreasheet
                        draft=Decimal(0.0), 
                        beam=Decimal(0.0), 
                        weight=Decimal(0.0), 
                        pct_interest=100, 
                    )
                    rego_aa_created.append(rego_no)
                else:
                    try:
                        vessel_details = VesselDetails.objects.get(vessel__rego_no=rego_no)
                        owner = Owner.objects.get(emailuser=user.id)
                        vessel_ownership = VesselOwnership.objects.filter(owner=owner, vessel__rego_no=rego_no).order_by("-created").first()
                        if not vessel_ownership:
                            vessel, vessel_details, vessel_ownership = self._create_single_vessel(
                                user.id, 
                                rego_no, 
                                ves_name=vessel_name, # use vessel_name from AA Moorings Spreasheet
                                ves_type=vessel_type,
                                length=vessel_length, # use vessel_length from AA Moorings Spreasheet
                                draft=Decimal(0.0), 
                                beam=Decimal(0.0), 
                                weight=Decimal(0.0), 
                                pct_interest=100, 
                            )
                    except Exception as e:
                        vessel, vessel_details, vessel_ownership = self._create_single_vessel(
                            user.id, 
                            rego_no, 
                            ves_name=vessel_name, # use vessel_name from AA Moorings Spreasheet
                            ves_type=vessel_type,
                            length=vessel_length, # use vessel_length from AA Moorings Spreasheet
                            draft=Decimal(0.0), 
                            beam=Decimal(0.0), 
                            weight=Decimal(0.0), 
                            pct_interest=100, 
                        )

                # update length from AA Spreadsheet file
                vessel_details.vessel_name=vessel_name
                vessel_details.vessel_length=Decimal(vessel_length) if vessel_length else Decimal(0)
                vessel_details.save()

                total_aa_created.append(rego_no)

                try:
                    lodgement_date = datetime.datetime.strptime(date_created, '%d/%m/%Y %H:%M %p').astimezone(datetime.timezone.utc)
                except Exception as e:
                    errors.append("lodgement_date substituted with general start date: " + str(e))
                    lodgement_date = datetime.datetime.strptime(date_applied, '%Y-%m-%d').astimezone(datetime.timezone.utc)

                status = 'approved'
                if not sticker_no:
                    status = 'printing_sticker'

                proposal=AnnualAdmissionApplication.objects.create(
                    proposal_type_id=ProposalType.objects.get(code='new').id, # new application
                    submitter=user.id,
                    lodgement_date=lodgement_date,
                    migrated=True,
                    vessel_details=vessel_details,
                    vessel_ownership=vessel_ownership,
                    rego_no=rego_no,
                    vessel_type=vessel_details.vessel_type,
                    vessel_name=vessel_details.vessel_name,
                    vessel_length=vessel_details.vessel_length,
                    vessel_draft=vessel_details.vessel_draft,
                    vessel_weight=vessel_details.vessel_weight,
                    percentage=vessel_ownership.percentage,
                    berth_mooring='',
                    individual_owner=True,
                    processing_status=status,
                    customer_status=status,
                    proposed_issuance_approval={
                        "start_date": start_date.strftime('%d/%m/%Y'),
                        "expiry_date": expiry_date.strftime('%d/%m/%Y'),
                        "details": None,
                        "cc_email": None,
                    },
                )

                proposal_applicant = self.create_proposal_applicant_aa(proposal, user, row)

                create_application_fee(proposal)

                ua=ProposalUserAction.objects.create(
                    proposal=proposal,
                    who=user.id,
                    what='Annual Admission - Migrated Application',
                )

                approval = AnnualAdmissionPermit.objects.create(
                    status='current',
                    current_proposal=proposal,
                    issue_date = TODAY, #TODO get actual
                    start_date = start_date, #TODO get actual
                    expiry_date = expiry_date,
                    submitter=user.id,
                    migrated=True,
                    export_to_mooring_booking=True,
                )

                aua=ApprovalUserAction.objects.create(
                    approval=approval,
                    who=user.id,
                    what='Annual Admission - Migrated Application',
                )

                proposal.approval = approval
                proposal.save()

                approval_history = ApprovalHistory.objects.create(
                    reason='new',
                    approval=approval,
                    vessel_ownership = vessel_ownership,
                    proposal = proposal,
                    start_date = start_date,
                )

                if sticker_no:
                    sticker = Sticker.objects.create(
                        number=sticker_no,
                        status=Sticker.STICKER_STATUS_CURRENT,
                        approval=approval,
                        proposal_initiated=proposal,
                        vessel_ownership=vessel_ownership,
                        printing_date=datetime.datetime.strptime(date_created.split(' ')[0], '%d/%m/%Y').date() if date_created else None,
                        mailing_date=datetime.datetime.strptime(date_created.split(' ')[0], '%d/%m/%Y').date() if date_created else None,
                        sticker_printing_batch=None,
                        sticker_printing_response=None,
                        postal_address_line1=proposal_applicant.postal_address_line1,
                        postal_address_locality=proposal_applicant.postal_address_locality,
                        postal_address_state=proposal_applicant.postal_address_state,
                        postal_address_country=proposal_applicant.postal_address_country,
                        postal_address_postcode=proposal_applicant.postal_address_postcode,
                    )
                else:
                    #create non-exported sticker record
                    sticker = Sticker.objects.create(
                        approval=approval,
                        proposal_initiated=proposal,
                        vessel_ownership=vessel_ownership,
                        postal_address_line1=proposal_applicant.postal_address_line1,
                        postal_address_locality=proposal_applicant.postal_address_locality,
                        postal_address_state=proposal_applicant.postal_address_state,
                        postal_address_country=proposal_applicant.postal_address_country,
                        postal_address_postcode=proposal_applicant.postal_address_postcode,
                    )

            except Exception as e:
                errors.append("Rego No " + str(rego_no) + " - User Id " + str(user.id) + ":" + str(e))

        print(f'rego_aa_created: {len(rego_aa_created)}')
        print(f'total_aa_created: {len(total_aa_created)}')
        print(f'Vessel Details Not Found: {vessel_details_not_found}')
        print(f'Vessel Details Not Found: {len(vessel_details_not_found)}')
        for i in errors:
            print(i)
        
        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nMigrate Annual Admissions Summary\n")
        f.write("Migrate Annual Admissions started at: {}\n".format(start_time))

        f.write(f'\nrego_aa_created: {len(rego_aa_created)}')
        f.write(f'\ntotal_aa_created: {len(total_aa_created)}')
        f.write(f'\nVessel Details Not Found: {vessel_details_not_found}')
        f.write(f'\nVessel Details Not Found: {len(vessel_details_not_found)}')
        if errors:
            f.write('\n\naa error details\n')
            for i in errors:
                f.write("\n"+i)

        f.write("\n\nTime taken for migrating annual admissions: {}s".format(end_time-start_time))
        f.close()

    def create_licence_pdfs(self):
        self.create_pdf_ml()
        self.create_pdf_aup()
        self.create_pdf_wl()
        self.create_pdf_aa()
        self.create_pdf_dcv()
    
    def create_pdf_ml(self):
        """ MooringLicenceReader.create_pdf_ml()
        """
        start_time = time.time()
        self._create_pdf_licence(MooringLicence.objects.filter(migrated=True))

        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nCreate Mooring License PDFs Summary\n")
        f.write("Create Mooring License PDFs started at: {}\n".format(start_time))
        f.write("\nTime taken for creating mooring license pdfs: {}s".format(end_time-start_time))
        f.close()

    def create_pdf_aup(self):
        """ MooringLicenceReader.create_pdf_aup()
        """
        start_time = time.time()
        self._create_pdf_licence(AuthorisedUserPermit.objects.filter(migrated=True))

        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nCreate Authorised User Permit PDFs Summary\n")
        f.write("Create Authorised User Permit PDFs started at: {}\n".format(start_time))
        f.write("\nTime taken for creating authorised user permit pdfs: {}s".format(end_time-start_time))
        f.close()

    def create_pdf_wl(self):
        """ MooringLicenceReader.create_pdf_wl()
        """
        start_time = time.time()
        self._create_pdf_licence(WaitingListAllocation.objects.filter(migrated=True))

        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nCreate Waiting List Allocation PDFs Summary\n")
        f.write("Create Waiting List Allocation PDFs started at: {}\n".format(start_time))
        f.write("\nTime taken for creating waiting list allocation pdfs: {}s".format(end_time-start_time))
        f.close()

    def create_pdf_aa(self):
        """ MooringLicenceReader.create_pdf_aa()
        """
        start_time = time.time()
        self._create_pdf_licence(AnnualAdmissionPermit.objects.filter(migrated=True))

        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nCreate Annual Admission PDFs Summary\n")
        f.write("Create Annual Admission PDFs started at: {}\n".format(start_time))
        f.write("\nTime taken for creating annual admission pdfs: {}s".format(end_time-start_time))
        f.close()

    def create_pdf_dcv(self):
        """ MooringLicenceReader.create_pdf_dcv()
        """
        start_time = time.time()
        self._create_pdf_licence(DcvPermit.objects.filter(migrated=True))

        end_time = time.time()
        f = open(self.summary_file, "a")
        f.write("\n\nCreate DCV Permit PDFs Summary\n")
        f.write("Create DCV Permit PDFs started at: {}\n".format(start_time))
        f.write("\nTime taken for creating dcv permit pdfs: {}s".format(end_time-start_time))
        f.close()

    @staticmethod
    def _create_pdf_licence(approvals_migrated):
        """ MooringLicenceReader._create_pdf_licence(MooringLicence.objects.filter(migrated=True), current_proposal__processing_status=Proposal.PROCESSING_STATUS_APPROVED)
        """
        if len(approvals_migrated) > 0:
            permit_name = approvals_migrated[0].__class__.__name__
            print(f'Total {permit_name}: {approvals_migrated.count()} - {approvals_migrated}')
            if isinstance(approvals_migrated[0], DcvPermit):
                approvals = approvals_migrated.filter(migrated=True)
            else:
                approvals = approvals_migrated.filter(migrated=True).filter(Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_APPROVED)|Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_PRINTING_STICKER))

            for idx, a in enumerate(approvals):
                try:
                    if isinstance(a, DcvPermit) and len(a.dcv_permit_documents.all())==0:
                        a.generate_dcv_permit_doc()
                    elif not hasattr(a, 'licence_document') or a.licence_document is None: 
                        a.generate_doc()
                        #retroactively update history (update last history record of approval)
                        history = a.approvalhistory_set.last()
                        history.approval_letter = a.licence_document
                        history.save()
                    print(f'{idx}, Created PDF for {permit_name}: {a}')
                except Exception as e:
                    logger.error(e)


def create_application_fee(proposal):

    application_fee = ApplicationFee.objects.create(proposal=proposal, created_by=255, payment_type=ApplicationFee.PAYMENT_TYPE_TEMPORARY)
    lines, db_processes_after_success = proposal.create_fee_lines()
    new_fee_calculation = FeeCalculation.objects.create(uuid=application_fee.uuid, data=db_processes_after_success)

    db_operations = new_fee_calculation.data

    if 'for_existing_invoice' in db_operations and db_operations['for_existing_invoice']:
        # For existing invoices, fee_item_application_fee.amount_paid should be updated, once paid
        for idx in db_operations['fee_item_application_fee_ids']:
            fee_item_application_fee = FeeItemApplicationFee.objects.get(id=int(idx))
            fee_item_application_fee.amount_paid = fee_item_application_fee.amount_to_be_paid
            fee_item_application_fee.save()
    else:

        if 'fee_item_id' in db_operations:
            fee_items = FeeItem.objects.filter(id=db_operations['fee_item_id'])
            if fee_items:
                amount_paid = None
                amount_to_be_paid = None
                if 'fee_amount_adjusted' in db_operations:
                    fee_amount_adjusted = db_operations['fee_amount_adjusted']
                    amount_to_be_paid = Decimal(fee_amount_adjusted)
                    amount_paid = amount_to_be_paid
                    fee_item = fee_items.first()
                fee_item_application_fee = FeeItemApplicationFee.objects.create(
                    fee_item=fee_item,
                    application_fee=application_fee,
                    vessel_details=proposal.vessel_details,
                    amount_to_be_paid=amount_to_be_paid,
                    amount_paid=amount_paid,
                )
                logger.info(f'FeeItemApplicationFee: [{fee_item_application_fee}] created.')
        if isinstance(db_operations, list):
            for item in db_operations:
                fee_item = FeeItem.objects.get(id=item['fee_item_id'])
                fee_amount_adjusted = item['fee_amount_adjusted']
                amount_to_be_paid = Decimal(fee_amount_adjusted)
                amount_paid = amount_to_be_paid
                vessel_details_id = item['vessel_details_id']  # This could be '' when null vessel application
                vessel_details = VesselDetails.objects.get(id=vessel_details_id) if vessel_details_id else None
                fee_item_application_fee = FeeItemApplicationFee.objects.create(
                    fee_item=fee_item,
                    application_fee=application_fee,
                    vessel_details=vessel_details,
                    amount_to_be_paid=amount_to_be_paid,
                    amount_paid=amount_paid,
                )
                logger.info(f'FeeItemApplicationFee: [{fee_item_application_fee}] has been created.')