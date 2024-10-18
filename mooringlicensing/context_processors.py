from mooringlicensing import settings
from ledger_api_client import utils as ledger_api_utils

def mooringlicensing_processor(request):

    web_url = request.META.get('HTTP_HOST', None)
    lt = ledger_api_utils.get_ledger_totals()

    return {
        'public_url': web_url,
        'template_group': 'ria',
        'LEDGER_UI_URL': f'{settings.LEDGER_UI_URL}',
        'LEDGER_SYSTEM_ID': f'{settings.LEDGER_SYSTEM_ID}',
        'ledger_totals': lt,
    }
