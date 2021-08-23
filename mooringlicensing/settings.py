from django.core.exceptions import ImproperlyConfigured

import os
from confy import env
import confy
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
confy.read_environment_file(BASE_DIR+"/.env")
os.environ.setdefault("BASE_DIR", BASE_DIR)

from ledger.settings_base import *

ROOT_URLCONF = 'mooringlicensing.urls'
SITE_ID = 1
DEPT_DOMAINS = env('DEPT_DOMAINS', ['dpaw.wa.gov.au', 'dbca.wa.gov.au'])
SYSTEM_MAINTENANCE_WARNING = env('SYSTEM_MAINTENANCE_WARNING', 24) # hours
DISABLE_EMAIL = env('DISABLE_EMAIL', False)
SHOW_TESTS_URL = env('SHOW_TESTS_URL', False)
SHOW_DEBUG_TOOLBAR = env('SHOW_DEBUG_TOOLBAR', False)

if SHOW_DEBUG_TOOLBAR:

    def show_toolbar(request):
        return True

    MIDDLEWARE_CLASSES += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
    INSTALLED_APPS += (
        'debug_toolbar',
    )
    INTERNAL_IPS = ('127.0.0.1', 'localhost')

    # this dict removes check to dtermine if toolbar should display --> works for rks docker container
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK" : show_toolbar,
        'INTERCEPT_REDIRECTS': False,
    }

STATIC_URL = '/static/'


INSTALLED_APPS += [
    'reversion_compare',
    'bootstrap3',
    'mooringlicensing',
    'mooringlicensing.components.main',
    'mooringlicensing.components.emails',
    'mooringlicensing.components.organisations',
    'mooringlicensing.components.users',
    'mooringlicensing.components.proposals',
    'mooringlicensing.components.approvals',
    'mooringlicensing.components.compliances',
    'mooringlicensing.components.payments_ml',
    'taggit',
    'rest_framework',
    'rest_framework_datatables',
    'rest_framework_gis',
    'reset_migrations',
    'ckeditor',
]

ADD_REVERSION_ADMIN=True

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_datatables.renderers.DatatablesRenderer',
    ),
}

MIDDLEWARE_CLASSES += [
    'mooringlicensing.middleware.FirstTimeNagScreenMiddleware',
    'mooringlicensing.middleware.RevisionOverrideMiddleware',
    'mooringlicensing.middleware.CacheControlMiddleware',
]

TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'mooringlicensing', 'templates'))
TEMPLATES[0]['OPTIONS']['context_processors'].append('mooringlicensing.context_processors.mooringlicensing_processor')
del BOOTSTRAP3['css_url']
#BOOTSTRAP3 = {
#    'jquery_url': '//static.dpaw.wa.gov.au/static/libs/jquery/2.2.1/jquery.min.js',
#    'base_url': '//static.dpaw.wa.gov.au/static/libs/twitter-bootstrap/3.3.6/',
#    'css_url': 'ledger/css/bootstrap.min.css',
#    'theme_url': None,
#    'javascript_url': None,
#    'javascript_in_head': False,
#    'include_jquery': False,
#    'required_css_class': 'required-form-field',
#    'set_placeholder': False,
#}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'mooringlicensing', 'cache'),
    }
}
STATIC_ROOT=os.path.join(BASE_DIR, 'staticfiles_ml')
STATICFILES_DIRS.append(os.path.join(os.path.join(BASE_DIR, 'mooringlicensing', 'static')))
DEV_STATIC = env('DEV_STATIC',False)
DEV_STATIC_URL = env('DEV_STATIC_URL')
if DEV_STATIC and not DEV_STATIC_URL:
    raise ImproperlyConfigured('If running in DEV_STATIC, DEV_STATIC_URL has to be set')
DATA_UPLOAD_MAX_NUMBER_FIELDS = None
DEV_APP_BUILD_URL = env('DEV_APP_BUILD_URL')  # URL of the Dev app.js served by webpack & express

# Use git commit hash for purging cache in browser for deployment changes
#GIT_COMMIT_HASH = ''
#GIT_COMMIT_DATE = ''
#if  os.path.isdir(BASE_DIR+'/.git/') is True:
 #   GIT_COMMIT_DATE = os.popen('cd '+BASE_DIR+' ; git log -1 --format=%cd').read()
  #  GIT_COMMIT_HASH = os.popen('cd  '+BASE_DIR+' ; git log -1 --format=%H').read()
#if len(GIT_COMMIT_HASH) == 0: 
#    GIT_COMMIT_HASH = os.popen('cat /app/rand_hash').read()
#    if len(GIT_COMMIT_HASH) == 0:
#       print ("ERROR: No rand hash provided")
RAND_HASH = ''
if  os.path.isdir(BASE_DIR+'/.git/') is True:
    RAND_HASH = os.popen('cd  '+BASE_DIR+' ; git log -1 --format=%H').read()
if not len(RAND_HASH):
    RAND_HASH = os.popen('cat /app/rand_hash').read()
if len(RAND_HASH) == 0:
    print ("ERROR: No rand hash provided")

# Department details
SYSTEM_NAME = env('SYSTEM_NAME', 'Mooring Licensing')
SYSTEM_NAME_SHORT = env('SYSTEM_NAME_SHORT', 'ML')
SITE_PREFIX = env('SITE_PREFIX', '')
SITE_DOMAIN = env('SITE_DOMAIN', '')
SUPPORT_EMAIL = env('SUPPORT_EMAIL', 'mooringlicensing@' + SITE_DOMAIN).lower()
DEP_URL = env('DEP_URL','www.' + SITE_DOMAIN)
DEP_PHONE = env('DEP_PHONE','(08) 9219 9978')
DEP_PHONE_SUPPORT = env('DEP_PHONE_SUPPORT','(08) 9219 9000')
DEP_FAX = env('DEP_FAX','(08) 9423 8242')
DEP_POSTAL = env('DEP_POSTAL','Locked Bag 104, Bentley Delivery Centre, Western Australia 6983')
DEP_NAME = env('DEP_NAME','Department of Biodiversity, Conservation and Attractions')
DEP_NAME_SHORT = env('DEP_NAME_SHORT','DBCA')
RIA_NAME = env('RIA_NAME', 'Rottnest Island Authority (RIA)')
SITE_URL = env('SITE_URL', 'https://' + SITE_PREFIX + '.' + SITE_DOMAIN)
PUBLIC_URL=env('PUBLIC_URL', SITE_URL)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'no-reply@' + SITE_DOMAIN).lower()
MEDIA_APP_DIR = env('MEDIA_APP_DIR', 'mooringlicensing')
#ADMIN_GROUP = env('ADMIN_GROUP', 'MooringLicensing Admin')
ADMIN_GROUP = env('ADMIN_GROUP', 'Mooring Licensing - Admin')
CRON_RUN_AT_TIMES = env('CRON_RUN_AT_TIMES', '04:05')
CRON_EMAIL = env('CRON_EMAIL', 'cron@' + SITE_DOMAIN).lower()
CRON_NOTIFICATION_EMAIL = env('CRON_NOTIFICATION_EMAIL', NOTIFICATION_EMAIL).lower()
EMAIL_FROM = DEFAULT_FROM_EMAIL
os.environ['LEDGER_PRODUCT_CUSTOM_FIELDS'] = "('ledger_description','quantity','price_incl_tax','price_excl_tax','oracle_code')"

BASE_URL=env('BASE_URL')

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
    },
    'awesome_ckeditor': {
        'toolbar': 'Basic',
    },
}

CONSOLE_EMAIL_BACKEND = env('CONSOLE_EMAIL_BACKEND', False)
if CONSOLE_EMAIL_BACKEND:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

PAYMENT_SYSTEM_ID = env('PAYMENT_SYSTEM_ID', 'S517')
OSCAR_BASKET_COOKIE_OPEN = 'mooringlicensing_basket'
PS_PAYMENT_SYSTEM_ID = PAYMENT_SYSTEM_ID
PAYMENT_SYSTEM_PREFIX = env('PAYMENT_SYSTEM_PREFIX', PAYMENT_SYSTEM_ID.replace('S', '0'))

MOORING_BOOKINGS_API_KEY=env('MOORING_BOOKINGS_API_KEY')
MOORING_BOOKINGS_API_URL=env('MOORING_BOOKINGS_API_URL')

PROPOSAL_TYPE_NEW = 'new'
PROPOSAL_TYPE_RENEWAL = 'renewal'
PROPOSAL_TYPE_AMENDMENT = 'amendment'
PROPOSAL_TYPES_FOR_FEE_ITEM = [
    (PROPOSAL_TYPE_NEW, 'New Application'),
    (PROPOSAL_TYPE_AMENDMENT, 'Amendment'),
    (PROPOSAL_TYPE_RENEWAL, 'Renewal'),
]

#ASSESSOR_GROUPS = ['Mooring Licensing Assessor Group', ]
#APPROVER_GROUPS = ['Mooring Licensing Approver Group', ]
HTTP_HOST_FOR_TEST = 'localhost:8071'
APPLICATION_TYPE_DCV_PERMIT = {
    'code': 'dcvp',
    'description': 'DCV Permit',
    'oracle_code': 'T1 EXEMPT',
}
APPLICATION_TYPE_DCV_ADMISSION = {
    'code': 'dcv',
    'description': 'DCV Admission',
    'oracle_code': 'T1 EXEMPT',
}
LOGGING['loggers']['mooringlicensing'] = {
    'handlers': ['file'],
    'level': 'INFO'
}
GROUP_MOORING_LICENSING_ADMIN = 'Mooring Licensing - Admin'
GROUP_MOORING_LICENSING_PAYMENT_OFFICER = 'Mooring Licensing - Payment Officers'
GROUP_DCV_ASSESSOR_WAITING_LIST = 'Mooring Licensing - Assessors: Waiting List'
GROUP_DCV_ASSESSOR_ANNUAL_ADMISSION = 'Mooring Licensing - Assessors: Annual Admission'
GROUP_DCV_ASSESSOR_AUTHORISED_USER = 'Mooring Licensing - Assessors: Authorised User'
GROUP_DCV_ASSESSOR_MOORING_LICENCE = 'Mooring Licensing - Assessors: Mooring Licence'
GROUP_DCV_APPROVER_AUTHORISED_USER = 'Mooring Licensing - Approvers: Authorised User'
GROUP_DCV_APPROVER_MOORING_LICENCE = 'Mooring Licensing - Approvers: Mooring Licence'
GROUP_DCV_PERMIT_ADMIN = 'Mooring Licensing - DCV Permit Admin'  # DCV Permit notification is sent to the member of this group
CUSTOM_GROUPS = [
    GROUP_MOORING_LICENSING_ADMIN,
    GROUP_MOORING_LICENSING_PAYMENT_OFFICER,
    GROUP_DCV_ASSESSOR_WAITING_LIST,
    GROUP_DCV_ASSESSOR_ANNUAL_ADMISSION,
    GROUP_DCV_ASSESSOR_AUTHORISED_USER,
    GROUP_DCV_ASSESSOR_MOORING_LICENCE,
    GROUP_DCV_APPROVER_AUTHORISED_USER,
    GROUP_DCV_APPROVER_MOORING_LICENCE,
    GROUP_DCV_PERMIT_ADMIN,
]

# For NumberOfDaysSettings
CODE_DAYS_BEFORE_DUE_COMPLIANCE = 'ComplianceDueDate'
CODE_DAYS_BEFORE_END_OF_SIX_MONTH_PERIOD_ML = 'MLVesselNominateNotification'
CODE_DAYS_BEFORE_END_OF_SIX_MONTH_PERIOD_WLA = 'WLAVesselNominateNotification'
CODE_DAYS_BEFORE_PERIOD_MLA = 'MLApplicationSubmitNotification'
CODE_DAYS_IN_PERIOD_MLA = 'MLApplicationSubmitPeriod'
CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA = 'MLADocumentsSubmitPeriod'
CODE_DAYS_FOR_ENDORSER_AUA = 'AUAEndorseDeclinePeriod'
CODE_DAYS_FOR_RENEWAL = 'AAPAUPMLRenewalNotification'

TYPES_OF_CONFIGURABLE_NUMBER_OF_DAYS = [
    {
        'code': CODE_DAYS_BEFORE_DUE_COMPLIANCE,
        'name': 'Compliance due date',
        'description': 'Number of days before due date of compliance',
        'default': 28
    },
    {
        'code': CODE_DAYS_BEFORE_END_OF_SIX_MONTH_PERIOD_ML,
        'name': 'Vessel nominate notification for ML',
        'description': 'Number of days before end of six month period in which a new vessel is to be nominated for ML',
        'default': 28
    },
    {
        'code': CODE_DAYS_BEFORE_END_OF_SIX_MONTH_PERIOD_WLA,
        'name': 'Vessel nominate notification for WLA',
        'description': 'Number of days before end of six month period in which a new vessel is to be nominated for WLA',
        'default': 28
    },
    {
        'code': CODE_DAYS_BEFORE_PERIOD_MLA,
        'name': 'MLA application submit notification',
        'description': 'Number of days before end of period in which the mooring licence application needs to be submitted',
        'default': 14
    },
    {
        'code': CODE_DAYS_IN_PERIOD_MLA,
        'name': 'MLA application submit period',
        'description': 'Number of days in which the mooring licence application needs to be submitted.',
        'default': 28
    },  ### 1
    {
        'code': CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA,
        'name': 'MLA documents submit period',
        'description': 'Number of days in which the additional documents for a mooring licence application needs to be submitted.',
        'default': 28
    },  ### 2
    {
        'code': CODE_DAYS_FOR_ENDORSER_AUA,
        'name': 'AUA endorse/decline period',
        'description': 'Number of days after initial submit for the endorser to endorse/decline',
        'default': 28
    },
    {
        'code': CODE_DAYS_FOR_RENEWAL,
        'name': 'AAP, AUP and ML Renewal notification',
        'description': 'Number of days before expiry date of the approvals to email',
        'default': 28
    },
]

# Oracle codes
ORACLE_CODE_ID_WL = 'oracle_code_wl'
ORACLE_CODE_ID_AA = 'oracle_code_aa'
ORACLE_CODE_ID_AU = 'oracle_code_au'
ORACLE_CODE_ID_ML = 'oracle_code_ml'
ORACLE_CODE_ID_DCV_PERMIT = 'oracle_code_dcv_permit'
ORACLE_CODE_ID_DCV_ADMISSION = 'oracle_code_dcv_admission'
ORACLE_CODE_ID_REPLACEMENT_STICKER = 'oracle_code_replacement_sticker'
ORACLE_CODE_ID_MOORING_SWAP = 'oracle_code_mooring_swap'
ORACLE_CODES = [
    {
        'identifier': ORACLE_CODE_ID_WL,
        'name': 'Waiting list allocation fees',
        'code': 'T1 EXEMPT',
    },
    {
        'identifier': ORACLE_CODE_ID_AA,
        'name': 'Annual admission fees',
        'code': 'T1 EXEMPT',
    },
    {
        'identifier': ORACLE_CODE_ID_AU,
        'name': 'Authorised user fees',
        'code': 'T1 EXEMPT',
    },
    {
        'identifier': ORACLE_CODE_ID_ML,
        'name': 'Mooring licence fees',
        'code': 'T1 EXEMPT',
    },
    {
        'identifier': ORACLE_CODE_ID_DCV_PERMIT,
        'name': 'DCV permit fees',
        'code': 'T1 EXEMPT',
    },
    {
        'identifier': ORACLE_CODE_ID_DCV_ADMISSION,
        'name': 'DCV admission fees',
        'code': 'T1 EXEMPT',
    },
    {
        'identifier': ORACLE_CODE_ID_REPLACEMENT_STICKER,
        'name': 'Replacement sticker fees',
        'code': 'T1 EXEMPT',
    },
    {
        'identifier': ORACLE_CODE_ID_MOORING_SWAP,
        'name': 'Mooring swap fees',
        'code': 'T1 EXEMPT',
    },
]
