from mooringlicensing import settings


def mooringlicensing_processor(request):
    ret_dict = {}

    web_url = request.META.get('HTTP_HOST', None)

    return {
        'public_url': web_url,
        # 'template_group': 'parksv2',
        'template_group': 'ria',
        'LEDGER_UI_URL': f'{settings.LEDGER_UI_URL}',
        'LEDGER_SYSTEM_ID': f'{settings.LEDGER_SYSTEM_ID}',
    }


