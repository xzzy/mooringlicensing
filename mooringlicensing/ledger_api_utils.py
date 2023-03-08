from ledger_api_client import utils
from ledger_api_client.ledger_models import EmailUserRO

from mooringlicensing import settings
from mooringlicensing.components.main.decorators import basic_exception_handler


@basic_exception_handler
def retrieve_email_userro(email_user_id):
    return EmailUserRO.objects.get(id=email_user_id)


def get_invoice_payment_status(invoice_id):
    inv_props = utils.get_invoice_properties(invoice_id)
    invoice_payment_status = inv_props['data']['invoice']['payment_status']
    return invoice_payment_status


def get_invoice_url(invoice_reference, request):
    # return f'{settings.LEDGER_API_URL}/ledgergw/invoice-pdf/{settings.LEDGER_API_KEY}/{invoice_reference}'
    # return f'/ledger-toolkit-api/invoice-pdf/{invoice_reference}/'

    # We shouldn't use the URL below for the front-end, because it includes the LEDGER_API_KEY, rather access it via ledger-toolkit-api/invoice-pdf
    # f'{settings.LEDGER_API_URL}/ledgergw/invoice-pdf/{settings.LEDGER_API_KEY}/{invoice_reference}'
    return request.build_absolute_uri(f'/ledger-toolkit-api/invoice-pdf/{invoice_reference}/')
