from mixer.backend.django import mixer
from django.conf import settings
from importlib import import_module
from django.utils import timezone
from datetime import timedelta

from mooringlicensing.management.default_data_manager import DefaultDataManager
#from .models import *
from ledger.accounts.models import EmailUser, EmailUserManager
import random
import string
import json, io, os, sys
from rest_framework.test import (
        APIRequestFactory, 
        force_authenticate, 
        APITestCase,
        APILiveServerTestCase,
        RequestsClient,
        )
from rest_framework import status
from ledger.accounts.models import EmailUser, Address
from ledger.address.models import UserAddress
from requests.auth import HTTPBasicAuth
from mooringlicensing.components.proposals.models import (
        ProposalType,
        ApplicationType,
        ProposalAssessorGroup,
        ProposalStandardRequirement,
        MooringBay,
        )
from mooringlicensing.components.approvals.models import (
        Approval,
        )
from mooringlicensing.components.main.models import (
        GlobalSettings,
)
from mooringlicensing.components.payments_ml.models import (
        FeePeriod,
        FeeSeason,
        FeeItem,
        FeeConstructor,
        VesselSizeCategoryGroup,
        VesselSizeCategory,
        )
#from mooringlicensing.components.main.utils import retrieve_marine_parks
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler


class APITestSetup(APITestCase):
    fixtures = ['countries.json']

    def setUp(self):
        print("setup method")
        self.superAdminUN = 'test.superadmin@dbcatest.com'
        self.adminUN = 'test.admin@dbcatest.com'
        self.nonAdminUN = 'test.customer@dbcatest.com'
        superadminUser = None
        adminUser = None
        user = None
        eum = EmailUserManager()
        self.superadminUser = EmailUser.objects.create(email=self.superAdminUN, password="pass", is_staff=True, is_superuser=True)
        self.superadminUser.set_password('pass')
        self.superadminUser.save()
        self.adminUser  = EmailUser.objects.create(email=self.adminUN,password="pass",is_staff=True, is_superuser=False)
        self.adminUser.set_password('pass')
        self.adminUser.save()

        self.customer = EmailUser.objects.create(email=self.nonAdminUN, password="pass", is_staff=False, is_superuser=False)
        self.customer.set_password('pass')
        self.customer.save()
        # customer UserAddress
        user_address = UserAddress.objects.create(
                country_id= 'AU',
                #is_default_for_billing= True,
                #is_default_for_shipping= True,
                line1= '17 Dick Perry',
                #line2: '',
                #line3': u'',
                #line4': u'BENTLEY DELIVERY CENTRE',
                #notes': u'',
                #num_orders': 0,
                #phone_number': None,
                postcode= '6151',
                #'search_text': u'',
                state= 'WA',
                #title': u'',
                user_id= self.customer.id
                )

        customer_address = Address.objects.create(user=self.customer, oscar_address=user_address)
        self.customer.residential_address = customer_address
        self.customer.save()

        self.externalUser1 = 'test.customer1@dbcatest.com'
        self.customer1 = EmailUser.objects.create(email=self.externalUser1, password="pass", is_staff=False, is_superuser=False)
        self.customer1.set_password('pass')
        self.customer1.save()
        # customer1 UserAddress
        user1_address = UserAddress.objects.create(
                country_id= 'AU',
                line1= '17 Dick Perry',
                postcode= '6151',
                state= 'WA',
                user_id= self.customer1.id
                )

        customer1_address = Address.objects.create(user=self.customer1, oscar_address=user1_address)
        self.customer1.residential_address = customer1_address
        self.customer1.save()

        self.externalUser2 = 'test.customer2@dbcatest.com'
        self.customer2 = EmailUser.objects.create(email=self.externalUser2, password="pass", is_staff=False, is_superuser=False)
        self.customer2.set_password('pass')
        self.customer2.save()
        # customer2 UserAddress
        user2_address = UserAddress.objects.create(
                country_id= 'AU',
                line1= '17 Dick Perry',
                postcode= '6151',
                state= 'WA',
                user_id= self.customer2.id
                )

        customer2_address = Address.objects.create(user=self.customer2, oscar_address=user2_address)
        self.customer2.residential_address = customer2_address
        self.customer2.save()

        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

        # Create ProposalStandardRequirements
        ProposalStandardRequirement.objects.create(
                code='R1',
                text='Standard requirement 1'
                )
        ProposalStandardRequirement.objects.create(
                code='R2',
                text='Standard requirement 2'
                )
        ProposalStandardRequirement.objects.create(
                code='R3',
                text='Standard Apiary requirement 1'
                )
        ProposalStandardRequirement.objects.create(
                code='R4',
                text='Standard Apiary requirement 2'
                )
        ## create_proposal_data
        #self.apiary_application_type_id = ApplicationType.objects.get(name='Apiary').id
        #self.create_proposal_data = {
        #    u'profile': 132376, 
        #    u'application': self.apiary_application_type_id, 
        #    u'behalf_of': u'individual', 
        #    }
        #self.create_proposal_data_customer1 = {
        #    u'profile': 132377, 
        #    u'application': self.apiary_application_type_id, 
        #    u'behalf_of': u'individual', 
        #    }
        #self.create_proposal_data_customer2 = {
        #    u'profile': 132378, 
        #    u'application': self.apiary_application_type_id, 
        #    u'behalf_of': u'individual', 
        #    }
        ## Site transfer applications
        #self.site_transfer_application_type_id = ApplicationType.objects.get(name='Site Transfer').id
        #self.create_site_transfer_proposal_data = {
        #    u'profile': 132377, 
        #    u'application': self.site_transfer_application_type_id, 
        #    u'behalf_of': u'individual',
        #    #u'selected_licence_holder': u'firstname.lastname@test.com',
        #    }
        ## submit_proposal_data
        #with open('disturbance/tests/all_the_features_1.json', 'r') as features_file_1:
        #    self.all_the_features_1 = json.load(features_file_1)
        #with open('disturbance/tests/all_the_features_2.json', 'r') as features_file_2:
        #    self.all_the_features_2 = json.load(features_file_2)

        # Dates
        self.today = timezone.now().date()
        self.today_str = self.today.strftime('%d/%m/%Y')
        day_delta = timedelta(days=1)
        week_delta = timedelta(weeks=1)
        self.today_plus_1_day = self.today + day_delta
        self.today_plus_1_week = self.today + day_delta
        self.today_plus_26_weeks = self.today + (day_delta * 26)
        self.today_plus_1_day_str = self.today_plus_1_day.strftime('%d/%m/%Y')
        self.today_plus_1_week_str = self.today_plus_1_week.strftime('%d/%m/%Y')
        self.today_plus_26_weeks_str = self.today_plus_26_weeks.strftime('%d/%m/%Y')

        self.today_minus_1_week = self.today - week_delta
        self.today_minus_4_weeks = self.today - (week_delta * 4)

        ## Payment admin data
        fee_season = FeeSeason.objects.create(name="2021/22")
        fee_period_1 = FeePeriod.objects.create(
                fee_season=fee_season,
                name="Period1",
                start_date=self.today_minus_1_week
                )
        fee_period_2 = FeePeriod.objects.create(
                fee_season=fee_season,
                name="Period2",
                start_date=self.today_minus_4_weeks
                )

        for application_type in ApplicationType.objects.all():
            for vessel_size_category_group in VesselSizeCategoryGroup.objects.all():
                fee_constructor = FeeConstructor.objects.create(
                        application_type=application_type,
                        fee_season=fee_season,
                        vessel_size_category_group=vessel_size_category_group
                        )
        amount = 1
        for fee_item in FeeItem.objects.all():
            fee_item.amount = amount
            fee_item.save()
            amount += 1


        ## test doc
        path = os.path.join(settings.BASE_DIR, 'mooringlicensing', 'tests', 'test_doc.png')
        #with open('mooringlicensing/tests/test_doc.png', 'rb') as f:
            #test_doc_bytes = f.read()
        with io.open(path, 'rb') as f:
            test_doc_bytes = f.read()
            test_doc_stream = io.BytesIO(test_doc_bytes)
            test_doc_obj = TemporaryFileUploadHandler()
            test_doc_obj.new_file(
                    file_name='17. External - Waiting List Amendment Application.png', 
                    field_name='_file',
                    content_type='image/png', 
                    content_length=os.path.getsize(path)
                    )
            test_doc_obj.receive_data_chunk(
                    raw_data=test_doc_bytes,
                    start=0
                    )
            test_doc = test_doc_obj.file_complete(
                    file_size=os.path.getsize(path)
                    )

            self.rego_papers_data = {
                'action': ['save'], 
                'input_name': ['vessel-registration-documents'], 
                'filename': ['25. External - New Authorised User Application - Applicant.png'], 
                'csrfmiddlewaretoken': ['stgaXJXyvxINxyC3QreA3D5W9BcwRBkNkmumoFngYpd9guP4DlHtCNdITFqJVdyL'], 
                '_file': [test_doc]
            }

            self.electoral_roll_doc_data = {
                'action': ['save'], 
                'input_name': ['electoral-roll-documents'], 
                'filename': ['25. External - New Authorised User Application - Applicant.png'], 
                'csrfmiddlewaretoken': ['stgaXJXyvxINxyC3QreA3D5W9BcwRBkNkmumoFngYpd9guP4DlHtCNdITFqJVdyL'], 
                '_file': [test_doc]
            }



        ## Mooring Bays
        #retrieve_marine_parks()
        MooringBay.objects.create(name='Bay1', mooring_bookings_id=1)
        MooringBay.objects.create(name='Bay2', mooring_bookings_id=2)

        # Global settings
        #ApiaryGlobalSettings.objects.create(key='oracle_code_apiary_site_annual_rental_fee', value='sample')

        # Get data ready
        temp = DefaultDataManager()

    def random_email(self):
        """Return a random email address ending in dbca.wa.gov.au
        """
#        print time
#        time.sleep(5)
        # import time as systime
        # systime.sleep(2)
        s = ''.join(random.choice(string.ascii_letters) for i in range(80))
        return '{}@dbca.wa.gov.au'.format(s)


# write apiary_sites data to file
def json_filewriter_example():
    # open(os.path.join(sys.path[0], input_file), 'r')
    input_file = 'all_the_features_1.json'
    with io.open(os.path.join(sys.path[0], input_file), 'w', encoding="utf8") as json_file:
        data = json.dumps(d, ensure_ascii=False, encoding="utf8")
        json_file.write(unicode(data))

