from mooringlicensing import settings
from ledger_api_client import utils as ledger_api_utils
import hashlib
import uuid

def mooringlicensing_processor(request):

    web_url = request.META.get('HTTP_HOST', None)
    lt = ledger_api_utils.get_ledger_totals()

    checkouthash = None #hashlib.sha256(str(uuid.uuid4()).encode('utf-8')).hexdigest()
    sessionVal = None
    if 'payment_model' in request.session and 'payment_pk' in request.session:
        checkouthash =  hashlib.sha256(str(str(request.session["payment_model"])+str(request.session["payment_pk"])).encode('utf-8')).hexdigest()

    return {
        'public_url': web_url,
        'template_group': 'ria',
        'LEDGER_UI_URL': f'{settings.LEDGER_UI_URL}',
        'LEDGER_SYSTEM_ID': f'{settings.LEDGER_SYSTEM_ID}',
        'ledger_totals': lt,
        'checkouthash' : checkouthash,
    }
