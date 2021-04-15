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
]

TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'mooringlicensing', 'templates'))
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
GIT_COMMIT_HASH = ''
GIT_COMMIT_DATE = ''
if  os.path.isdir(BASE_DIR+'/.git/') is True:
    GIT_COMMIT_DATE = os.popen('cd '+BASE_DIR+' ; git log -1 --format=%cd').read()
    GIT_COMMIT_HASH = os.popen('cd  '+BASE_DIR+' ; git log -1 --format=%H').read()
if len(GIT_COMMIT_HASH) == 0: 
    GIT_COMMIT_HASH = os.popen('cat /app/git_hash').read()
    if len(GIT_COMMIT_HASH) == 0:
       print ("ERROR: No git hash provided")

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
SITE_URL = env('SITE_URL', 'https://' + SITE_PREFIX + '.' + SITE_DOMAIN)
PUBLIC_URL=env('PUBLIC_URL', SITE_URL)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'no-reply@' + SITE_DOMAIN).lower()
MEDIA_APP_DIR = env('MEDIA_APP_DIR', 'mooringlicensing')
ADMIN_GROUP = env('ADMIN_GROUP', 'MooringLicensing Admin')
CRON_RUN_AT_TIMES = env('CRON_RUN_AT_TIMES', '04:05')
CRON_EMAIL = env('CRON_EMAIL', 'cron@' + SITE_DOMAIN).lower()
EMAIL_FROM = DEFAULT_FROM_EMAIL

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

if env('CONSOLE_EMAIL_BACKEND', False):
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

PAYMENT_SYSTEM_ID = env('PAYMENT_SYSTEM_ID', 'S517')

MOORING_BOOKINGS_API_KEY=env('MOORING_BOOKINGS_API_KEY')
MOORING_BOOKINGS_API_URL=env('MOORING_BOOKINGS_API_URL')

PROPOSAL_TYPE_NEW = 'new'
PROPOSAL_TYPE_RENEWAL = 'renewal'
PROPOSAL_TYPE_AMENDMENT = 'amendment'
PROPOSAL_TYPES = [
    (PROPOSAL_TYPE_NEW, 'New Application'),
    (PROPOSAL_TYPE_AMENDMENT, 'Amendment'),
    (PROPOSAL_TYPE_RENEWAL, 'Renewal'),
]

ASSESSOR_GROUPS = ['Mooring Licensing Assessor Group', ]
APPROVER_GROUPS = ['Mooring Licensing Approver Group', ]
HTTP_HOST_FOR_TEST = 'localhost:8071'
APPLICATION_TYPE_DCV_PERMIT = {'code': 'dcvp', 'description': 'DCV Permit'}
LOGGING['loggers']['mooringlicensing'] = {
            'handlers': ['file'],
            'level': 'INFO'
        }
