from ledger.accounts.models import Organisation as ledger_organisation
from ledger.accounts.models import OrganisationAddress
from ledger.accounts.models import EmailUser, Address
from ledger.payments.models import Invoice
from django.conf import settings
#from disturbance.components.organisations.models import Organisation, OrganisationContact, UserDelegation
#from disturbance.components.main.models import ApplicationType
#from disturbance.components.main.utils import get_category
#from disturbance.components.proposals.models import Proposal, ProposalType, ApiarySite, ApiarySiteOnProposal, ProposalApiary #, ProposalOtherDetails, ProposalPark
#from disturbance.components.approvals.models import Approval, MigratedApiaryLicence, ApiarySiteOnApproval
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone
from ledger.address.models import Country
import csv
import os
import datetime
import time
import string
import pandas as pd
import numpy as np

from dateutil.relativedelta import relativedelta
from decimal import Decimal

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
)
from mooringlicensing.components.approvals.models import Approval, ApprovalHistory, MooringLicence, VesselOwnershipOnApproval



import logging
logger = logging.getLogger(__name__)

NL = '\n'

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

class MooringLicenceReader():
    """
    First need to run clean().
    This will write output files to /var/www/mooringlicensing/mooringlicensing/utils/csv/clean
        from mooringlicensing.utils.export_clean import clean
        clean()
        
        
    FROM shell_plus:
        from mooringlicensing.utils.migration_utils_pd import MooringLicenceReader
        mlr=MooringLicenceReader('/var/www/mooringlicensing/mooringlicensing/utils/csv/clean/PersonDets20221201-083245.txt', '/var/www/mooringlicensing/mooringlicensing/utils/csv/clean/MooringDets20221201-083202.txt', '/var/www/mooringlicensing/mooringlicensing/utils/csv/clean/VesselDets20221201-083245.txt')

        mlr.create_users()
        mlr.create_licences()
        mlr.create_licence_pdf()

    FROM mgt-command:
        python manage_ds.py mooring_migration_script --filename mooringlicensing/utils/csv/MooringDets20221201-083202.txt


    Check for unique permit numbers
        pm = df['permit_number'].value_counts().loc[lambda x: x>1][1:].astype('int')
        pm.to_excel('/tmp/permit_numbers.xlsx')

    """

    def __init__(self, fname_user, fname_ml, fname_ves):
        self.df_user=pd.read_csv(fname_user, delimiter='|', dtype=str, low_memory=False)
        self.df_ml=pd.read_csv(fname_ml, delimiter='|', dtype=str)
        self.df_ves=pd.read_csv(fname_ves, delimiter='|', dtype=str)

        self.df_user=self._read_users()
        self.df_ml=self._read_ml()
        self.df_ves=self._read_ves()

        # create_users
        self.pers_ids = []
        self.user_created = []
        self.user_existing = []
        self.user_errors = []
        self.no_email = []

        # create_vessels
        self.vessels_created = []
        self.vessels_existing = []
        self.vessels_errors = []
        self.pct_interest_errors = []
        self.pct_interest_errors = []
        self.no_ves_rows = []

    def __get_phone_number(self, row):
        try: 
            return row.phone_number.replace(' ', '')
        except: 
            return row.mobile_number.replace(' ', '')

    def __get_mobile_number(self, row):
        try: 
            return row.mobile_number.replace(' ', '')
        except: 
            return row.phone_number.replace(' ', '')

#    def _read_excel(self, filename):
#        def _get_country_code(x):
#            try:
#                country=Country.objects.get(iso_3166_1_a2=x.get('country'))
#            except Exception as e:
#                country=Country.objects.get(iso_3166_1_a2='AU')
#            return country.code
#
#
#        df = pd.read_excel(filename)
#
#        # Rename the cols from Spreadsheet headers to Model fields names
#        df = df.rename(columns=COLUMN_MAPPING)
#        df[df.columns] = df.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
#        #df['start_date']             = pd.to_datetime(df['start_date'], errors='coerce')
#        #df['expiry_date']            = pd.to_datetime(df['expiry_date'], errors='coerce')
#        #df['issue_date']             = pd.to_datetime(df['issue_date'], errors='coerce')
#        #df['approval_cpc_date']      = pd.to_datetime(df['approval_cpc_date'], errors='coerce')
#        #df['approval_minister_date'] = pd.to_datetime(df['approval_minister_date'], errors='coerce')
#
#        #df['issue_date'] = df.apply(lambda row: row.issue_date if isinstance(row.issue_date, datetime.datetime) else row.start_date, axis=1)
#        #df['abn']        = df['abn'].str.replace(" ","").str.strip()
#        #df['email']      = df['email'].str.replace(" ","").str.lower().str.strip()
#        #df['first_name'] = df['first_name'].apply(lambda x: x.lower().capitalize().strip() if not pd.isnull(x) else 'No First Name')
#        #df['last_name']  = df['last_name'].apply(lambda x: x.lower().capitalize().strip() if not pd.isnull(x) else 'No Last Name')
#        #df['licencee']   = df['licencee'].apply(lambda x: x.strip() if not pd.isnull(x) else 'No Licencee Name')
#        #df['postcode']   = df['postcode'].apply(lambda x: '0000' if pd.isnull(x) else x)
#        #df['country']    = df['country'].apply(_get_country_code)
# 
#        # clean everything else
#        df.fillna('', inplace=True)
#        df.replace({np.NaN: ''}, inplace=True)
#
#        # check excel column names are the same column_mappings
#        #import ipdb; ipdb.set_trace()
#        #if df.columns.values.tolist() != [*COLUMN_MAPPING.values()]:
#        #    raise Exception('Column Names have changed!')
#
#        # add extra column
#        #df['licencee_type'] = df['abn'].apply(lambda x: 'organisation' if x else 'individual')
#
#        #import ipdb; ipdb.set_trace()
#        #return df[:500]
#        return df

    def _read_users(self):
        def _get_country_code(x):
            try:
                country=Country.objects.get(iso_3166_1_a2=x.get('country'))
            except Exception as e:
                country=Country.objects.get(iso_3166_1_a2='AU')
            return country.code


        #import ipdb; ipdb.set_trace()
        # Rename the cols from Spreadsheet headers to Model fields names
        df_user = self.df_user.rename(columns=USER_COLUMN_MAPPING)
        df_user[df_user.columns] = df_user.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
 
        # clean everything else
        df_user.fillna('', inplace=True)
        df_user.replace({np.NaN: ''}, inplace=True)

        #return df[:500]
        return df_user

    def _read_ml(self):

        # Rename the cols from Spreadsheet headers to Model fields names
        df_ml = self.df_ml.rename(columns=ML_COLUMN_MAPPING)
        df_ml[df_ml.columns] = df_ml.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
 
        # clean everything else
        df_ml.fillna('', inplace=True)
        df_ml.replace({np.NaN: ''}, inplace=True)

        # filter cancelled and rows with no name
        #import ipdb; ipdb.set_trace()
        df_ml = df_ml[(df_ml['cancelled']=='N') & (df_ml['first_name_l'].isna()==False)]

        #return df[:500]
        return df_ml

    def _read_ves(self):

        # clean everything else
        self.df_ves.fillna('', inplace=True)
        self.df_ves.replace({np.NaN: ''}, inplace=True)

        # filter cancelled and rows with no name
        #df_ml = df_ml[(df_ml['cancelled']=='N') & (df_ml['first_name_l'].isna()==False)]

        #return df[:500]
        return self.df_ves



    def run_migration(self):

        # create the users and organisations, if they don't already exist
        t0_start = time.time()
        #try:
        self.create_users()
        self.create_organisations()
        #except Exception as e:
         #   print(e)
          #  import ipdb; ipdb.set_trace()
        t0_end = time.time()
        print('TIME TAKEN (Orgs and Users): {}'.format(t0_end - t0_start))

        # create the Migratiom models
        t1_start = time.time()
        #try:
        self.create_licences()
        #except Exception as e:
         #   print(e)
          #  import ipdb; ipdb.set_trace()
        t1_end = time.time()
        print('TIME TAKEN (Create License Models): {}'.format(t1_end - t1_start))

        # create the Licence/Permit PDFs
        t2_start = time.time()
        try:
            self.create_licence_pdf()
        except Exception as e:
            print(e)
            import ipdb; ipdb.set_trace()
        t2_end = time.time()
        print('TIME TAKEN (Create License PDFs): {}'.format(t2_end - t2_start))

        print('TIME TAKEN (Total): {}'.format(t2_end - t0_start))

    def create_users(self):
        # Iterate through the dataframe and create non-existent users
        #import ipdb; ipdb.set_trace()
        for index, row in self.df_ml.groupby('pers_no').first().iterrows():
            #if row.status != 'Vacant':
            try:
                #import ipdb; ipdb.set_trace()
                #first_name = data['first_name'] if not pd.isnull(data['first_name']) else 'No First Name'
                #last_name = data['last_name'] if not pd.isnull(data['last_name']) else 'No Last Name'
                #email = df['email']
                #import ipdb; ipdb.set_trace()
                if not row.name:
                    continue

                user_row = self.df_user[self.df_user['pers_no']==row.name] #.squeeze() # as Pandas Series
                if len(user_row)>1:
                    user_row = user_row[user_row['paid_up']=='Y']
                user_row = user_row.squeeze() # convert to Pandas Series

                email = user_row.email.lower().replace(' ','')
                if not email:
                    self.no_email.append(user_row.pers_no)
                    continue

                first_name = user_row.first_name.lower().capitalize().replace(' ','')
                last_name = user_row.last_name.lower().capitalize().replace(' ','')

                users = EmailUser.objects.filter(email=email)
                if users.count() == 0:
                    #import ipdb; ipdb.set_trace()
                    user = EmailUser.objects.create(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=self.__get_phone_number(user_row),
                        mobile_number=self.__get_mobile_number(user_row)
                    )

                    country = Country.objects.get(printable_name='Australia')
                    address, address_created = Address.objects.get_or_create(line1=user_row.address, locality=user_row.suburb, postcode=user_row.postcode, state=user_row.state, country=country, user=user)
                    user.residential_address = address
                    user.postal_address = address
                    user.save()
                    print(f'{email}: {user.postal_address}')
 
                    self.user_created.append(email)
                else:
                    user = users[0]
                    self.user_existing.append(email)
                
                self.pers_ids.append((user.id, row.name))


            except Exception as e:
                import ipdb; ipdb.set_trace()
                self.user_errors.append(user_row.email)
                logger.error(f'user: {row.name}   *********** 1 *********** FAILED. {e}')

        print(f'users created:  {len(self.user_created)}')
        print(f'users existing: {len(self.user_existing)}')
        print(f'users errors:   {len(self.user_errors)}')
        print(f'no_email errors:   {len(self.no_email)}')
        print(f'users errors:   {self.user_errors}')
        print(f'no_email errors:   {self.no_email}')

    def create_vessels(self):

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
            #return [i.rstrip(pers_no) for i in ves_list_raw if i.rstrip(pers_no)]  
            return [i[:-len(pers_no)] for i in ves_list_raw if i!=pers_no]  

        def ves_fields(ves_row):
#            VES_FIELDS=['Name','DoT Rego','Reg Length', 'Total Length','Type','Rego Expiry','%Interest','Reg Owners','Tonnage','Draft','Ins Expiry','Pub Liability','Sticker Col','Au Sites','Lic Sticker Number','Licencee Sticker Sent','Au Sticker No','Date Au Sticker Sent']
#            POSTFIX=['Nominated Ves','Ad Ves 2','Ad Ves 3','Ad Ves 4','Ad Ves 5','Ad Ves 6','Ad Ves 7']
#
#            ves_idx = []
#            for postfix in POSTFIX:
#                ves_list.append([field + ' ' + postfix for field in VES_FIELDS])
#                
# 
#            mlr.df_ves[mlr.df_ves['Person No'].isin(l2)]

            #import ipdb; ipdb.set_trace()
            ves_details = []
            for colname_postfix in ['Nominated Ves', 'Ad Ves 2', 'Ad Ves 3', 'Ad Ves 4', 'Ad Ves 5', 'Ad Ves 6', 'Ad Ves 7']:
                cols = [col for col in ves_row.columns if (colname_postfix in col)]
                #cols = [i.replace(colname_postfix+' ','') for i in cols]

                ves_detail = ves_row[cols].to_dict(orient='records')[0]

                if ves_row['Name ' + colname_postfix].iloc[0] != '':
                    ves_details.append(ves_detail)

            return ves_details

        def try_except(idx, success):
            #if pers_no=='213162':
            #    import ipdb; ipdb.set_trace()

            try:
                val = float(success[idx])
            except Exception:
                val = 0.00
            return val

        for user_id, pers_no in self.pers_ids:
            try:
                if pers_no=='000377':
                    import ipdb; ipdb.set_trace()

                ves_row = self.df_ves[self.df_ves['Person No']==pers_no+pers_no] # VesselDet doubles-up/appends pers_no in all columns
                ves_row = ves_row.apply(lambda x: x.str[:-len(pers_no)], axis = 1) # remove the double pers_no in each field
                if len(ves_row) > 1:
                    self.no_ves_rows.append((pers_no, len(ves_row)))

                ves_list = ves_fields(ves_row)

                import ipdb; ipdb.set_trace()
#                ves_names          = ves_fields('Name', ves_row, pers_no)
#                dot_regos          = ves_fields('DoT Rego', ves_row, pers_no)
#                reg_lengths        = ves_fields('Reg Length', ves_row, pers_no)
#                tot_lengths        = ves_fields('Total Length', ves_row, pers_no)
#                ves_types          = ves_fields('Type', ves_row, pers_no)
#                rego_expiries      = ves_fields('Rego Expiry', ves_row, pers_no)
#                perc_interest      = ves_fields('%Interest', ves_row, pers_no)
#                reg_owners         = ves_fields('Reg Owners', ves_row, pers_no)
#                tonnages           = ves_fields('Tonnage', ves_row, pers_no)
#                drafts             = ves_fields('Draft', ves_row, pers_no)
#                ins_expiries       = ves_fields('Ins Expiry', ves_row, pers_no)
#                ins_pub_liability  = ves_fields('Pub Liability', ves_row, pers_no)
#                sticker_cols       = ves_fields('Sticker Col', ves_row, pers_no)
#                au_sites           = ves_fields('Au Sites', ves_row, pers_no)
#                sticker_numbers    = ves_fields('Lic Sticker Number', ves_row, pers_no)
#                sticker_sent       = ves_fields('Licencee Sticker Sent', ves_row, pers_no)
#                au_sticker_numbers = ves_fields('Au Sticker No', ves_row, pers_no)
#                au_sticker_sent    = ves_fields('Date Au Sticker Sent', ves_row, pers_no)

                try:
                    owner = Owner.objects.get(emailuser_id=user_id)
                except ObjectDoesNotExist:
                    owner = Owner.objects.create(emailuser_id=user_id)

                vessels = []
                for i, ves in enumerate(ves_list):
                    try:
                        vessel = Vessel.objects.get(rego_no=dot_regos[i])
                    except ObjectDoesNotExist:
                        vessel = Vessel.objects.create(rego_no=dot_regos[i])

                    try:
                        vessel_ownership = VesselOwnership.objects.get(owner=owner, vessel=vessel)
                    except ObjectDoesNotExist:
                        pct_interest = int(round(float(try_except(i, perc_interest)),0))
                        if pct_interest < 25:
                            self.pct_interest_errors.append((pers_no, dot_regos[i], pct_interest))
                            pct_interest = 100
                        vessel_ownership = VesselOwnership.objects.create(owner=owner, vessel=vessel, percentage=pct_interest)

                    try:
                        vessel_details = VesselDetails.objects.get(vessel=vessel)
                    except MultipleObjectsReturned:
                        vessel_details = VesselDetails.objects.filter(vessel=vessel)[0]
                    #except ObjectDoesNotExist:
                    except:
                        vessel_details = VesselDetails.objects.create(
                            vessel=vessel,
                            vessel_type=ves_types[i],
                            vessel_name=ves_names[i],
                            vessel_length=try_except(i, tot_lengths),
                            vessel_draft=try_except(i, drafts),
                            vessel_weight=try_except(i, tonnages),
                            berth_mooring=''
                        )
                    vessels.append(dot_regos[i])
                self.vessels_created.append((pers_no, len(vessels), vessels))

            except Exception as e:
                self.vessels_errors.append((pers_no, str(e)))
                continue

        print(f'vessels created:  {len(self.vessels_created)}')
        print(f'vessels errors:   {self.vessels_errors}')
        print(f'vessels errors:   {len(self.vessels_errors)}')
        print(f'vessels pct_int errors:   {self.pct_interest_errors}')
        print(f'vessels pct_int errors:   {len(self.pct_interest_errors)}')
        print(f'vessels no_ves_rows: {self.no_ves_rows}: Total len({self.no_ves_rows})')


    def create_licences(self):
        count = 1
        completed_site_numbers = []
        duplicate_site_numbers = []
        skipped_indices = []
        with transaction.atomic():
            #for index, row in self.df[3244:].iterrows():
            for index, row in self.df.iterrows():
                try:
                    # TODO: remove once migration file has been corrected
                    # temp solution for vacant sites causing error
                    #if index in [3823, 6517]:
                     #   continue
                    site_number = None
                    # TODO: remove once migration file has been corrected
                    #if not row.permit_number and not row.licensed_site:
                    #    skipped_indices.append(index)
                    #    continue
                    #    raise ValueError("index: {} has no permit_number or licenced_site".format(index))
                    site_number = int(row.permit_number) if row.permit_number else int(row.licensed_site)
                    #ApiarySite.objects.filter(id=site_number)
                    if site_number not in completed_site_numbers and \
                        not ApiarySite.objects.filter(id=site_number).exists():

                        #if row.status != 'Vacant' and index>4474:
                        #if row.status != 'Vacant':
                            #import ipdb; ipdb.set_trace()
                        if row.licencee_type == 'organisation':
                            org = Organisation.objects.get(organisation__abn=row.abn)
                            user = EmailUser.objects.get(email=row.email)
                            self._migrate_approval(data=row, submitter=user, applicant=org, proxy_applicant=None)
                            print("Permit number {} migrated".format(row.get('permit_number')))
                            print
                            print

                        elif row.licencee_type == 'individual':
                            user = EmailUser.objects.get(email=row.email)
                            self._migrate_approval(data=row, submitter=user, applicant=None, proxy_applicant=user)
                            print("Permit number {} migrated".format(row.get('permit_number')))

                        else:
                            # declined and not to be reissued
                            status = data['status']

                        completed_site_numbers.append(site_number)
                        count += 1

                        print()
                        print(f'******************************************************** INDEX: {index}')
                        print()
                    else:
                        duplicate_site_numbers.append(site_number)

                except ValueError as e:
                    print(f'ERROR: SITE NUMBER {site_number} - SKIPPING')
                    import ipdb; ipdb.set_trace()
                    raise e
                except Exception as e:
                    print(e)
                    import ipdb; ipdb.set_trace()
                    raise e

        print(f'Duplicate Site Numbers: {duplicate_site_numbers}')
        print('Skipped indices: {}'.format(skipped_indices))

    def _migrate_approval(self, data, submitter, applicant=None, proxy_applicant=None):
        from disturbance.components.approvals.models import Approval
        #import ipdb; ipdb.set_trace()
        try:
            site_number = int(data.permit_number) if data.permit_number else int(data.licensed_site)
        except Exception as e:
            import ipdb; ipdb.set_trace()
            print('ERROR: There is no site_number - Must provide a site number in migration spreadsheeet. {e}')

        try:
            expiry_date = data['expiry_date'] if data['expiry_date'] else datetime.date.today()
            start_date = data['start_date'] if data['start_date'] else datetime.date.today()
            issue_date = data['issue_date'] if data['issue_date'] else start_date
            site_status = 'not_to_be_reissued' if data['status'].lower().strip() == 'not to be reissued' else data['status'].lower().strip()

        except Exception as e:
            import ipdb; ipdb.set_trace()
            print(e)

        try:

            #import ipdb; ipdb.set_trace()
            if applicant:
                proposal, p_created = Proposal.objects.get_or_create(
                                application_type=self.application_type,
                                activity='Apiary',
                                submitter=submitter,
                                applicant=applicant,
                                schema=self.proposal_type.schema,
                            )
                approval, approval_created = Approval.objects.update_or_create(
                                applicant=applicant,
                                status=Approval.STATUS_CURRENT,
                                apiary_approval=True,
                                defaults = {
                                    'issue_date':issue_date,
                                    'expiry_date':expiry_date,
                                    'start_date':start_date,
                                    #'submitter':submitter,
                                    'current_proposal':proposal,
                                    }
                            )
            else:
                import ipdb; ipdb.set_trace()

            #if 'PM' not in proposal.lodgement_number:
            #    proposal.lodgement_number = proposal.lodgement_number.replace('P', 'PM') # Application Migrated
            proposal.approval= approval
            proposal.processing_status='approved'
            proposal.customer_status='approved'
            proposal.migrated=True
            proposal.proposed_issuance_approval = {
                    'start_date': start_date.strftime('%d-%m-%Y'),
                    'expiry_date': expiry_date.strftime('%d-%m-%Y'),
                    'details': 'Migrated',
                    'cc_email': 'Migrated',
            }

            approval.migrated=True

            # create invoice for payment of zero dollars
            order = create_invoice(proposal)
            invoice = Invoice.objects.get(order_number=order.number) 
            proposal.fee_invoice_references = [invoice.reference]

            proposal.save()
            approval.save()

            # create apiary sites and intermediate table entries
            #geometry = GEOSGeometry('POINT(' + str(data['latitude']) + ' ' + str(data['longitude']) + ')', srid=4326)
            geometry = GEOSGeometry('POINT(' + str(data['latitude']) + ' ' + str(data['longitude']) + ')', srid=4326)
            #import ipdb; ipdb.set_trace()
            apiary_site = ApiarySite.objects.create(
                    id=site_number,
                    is_vacant=True if site_status=='vacant' else False
                    )
            site_category = get_category(geometry)
            intermediary_approval_site = ApiarySiteOnApproval.objects.create(
                                            #id=site_number,
                                            apiary_site=apiary_site,
                                            approval=approval,
                                            wkb_geometry=geometry,
                                            site_category = site_category,
                                            licensed_site=True if data['licensed_site'] else False,
                                            batch_no=data['batch_no'],
                                            approval_cpc_date=data['approval_cpc_date'] if data.approval_cpc_date else None,
                                            approval_minister_date=data['approval_minister_date'] if data.approval_minister_date else None,
                                            map_ref=data['map_ref'],
                                            forest_block=data['forest_block'],
                                            cog=data['cog'],
                                            roadtrack=data['roadtrack'],
                                            zone=data['zone'],
                                            catchment=data['catchment'],
                                            #dra_permit=data['dra_permit'],
                                            site_status=site_status,
                                            )
            #import ipdb; ipdb.set_trace()
            pa, pa_created = ProposalApiary.objects.get_or_create(proposal=proposal)

            intermediary_proposal_site = ApiarySiteOnProposal.objects.create(
                                            #id=site_number,
                                            apiary_site=apiary_site,
                                            #approval=approval,
                                            proposal_apiary=pa,
                                            wkb_geometry_draft=geometry,
                                            site_category_draft = site_category,
                                            wkb_geometry_processed=geometry,
                                            site_category_processed = site_category,
                                            licensed_site=True if data['licensed_site'] else False,
                                            batch_no=data['batch_no'],
                                            #approval_cpc_date=data['approval_cpc_date'],
                                            #approval_minister_date=data['approval_minister_date'],
                                            approval_cpc_date=data['approval_cpc_date'] if data.approval_cpc_date else None,
                                            approval_minister_date=data['approval_minister_date'] if data.approval_minister_date else None,
                                            map_ref=data['map_ref'],
                                            forest_block=data['forest_block'],
                                            cog=data['cog'],
                                            roadtrack=data['roadtrack'],
                                            zone=data['zone'],
                                            catchment=data['catchment'],
                                            site_status=site_status,
                                            #dra_permit=data['dra_permit'],
                                            )
            #import ipdb; ipdb.set_trace()

            apiary_site.latest_approval_link=intermediary_approval_site
            apiary_site.latest_proposal_link=intermediary_proposal_site
            if site_status == 'vacant':
                apiary_site.approval_link_for_vacant=intermediary_approval_site
                apiary_site.proposal_link_for_vacant=intermediary_proposal_site
            apiary_site.save()


        except Exception as e:
            logger.error('{}'.format(e))
            import ipdb; ipdb.set_trace()
            return None

        return approval

    def create_licence_pdf(self):
        approvals_migrated = Approval.objects.filter(current_proposal__application_type__name=ApplicationType.APIARY, migrated=True)
        print('Total Approvals: {} - {}'.format(approvals_migrated.count(), approvals_migrated))
        for idx, a in enumerate(approvals_migrated):
            a.generate_doc(a.current_proposal.submitter)
            print('{}, Created PDF for Approval {}'.format(idx, a))



def create_invoice(proposal, payment_method='other'):
        """
        This will create and invoice and order from a basket bypassing the session
        and payment bpoint code constraints.
        """
        from ledger.checkout.utils import createCustomBasket
        from ledger.payments.invoice.utils import CreateInvoiceBasket
        from ledger.accounts.models import EmailUser

        now = timezone.now().date()
        line_items = [
            {'ledger_description': 'Migration Licence Charge Waiver - {} - {}'.format(now, proposal.lodgement_number),
             'oracle_code': 'N/A', #proposal.application_type.oracle_code_application,
             'price_incl_tax':  Decimal(0.0),
             'price_excl_tax':  Decimal(0.0),
             'quantity': 1,
            }
        ]

        user = EmailUser.objects.get(email__icontains='das@dbca.wa.gov.au')
        invoice_text = 'Migrated Permit/Licence Invoice'

        basket  = createCustomBasket(line_items, user, settings.PAYMENT_SYSTEM_ID)
        order = CreateInvoiceBasket(payment_method=payment_method, system=settings.PAYMENT_SYSTEM_PREFIX).create_invoice_and_order(basket, 0, None, None, user=user, invoice_text=invoice_text)

        return order
    


