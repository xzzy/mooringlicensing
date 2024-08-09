from ledger_api_client import utils
from ledger_api_client.ledger_models import EmailUserRO
from ledger_api_client.managed_models import SystemUser
from ledger_api_client import api
from io import StringIO
import json
import logging
from mooringlicensing.components.main.decorators import basic_exception_handler

logger = logging.getLogger(__name__)


@basic_exception_handler
def retrieve_email_userro(email_user_id):
    try:
        return EmailUserRO.objects.get(id=email_user_id)
    except Exception as e:
        print(e)

@basic_exception_handler
def retrieve_system_user(email_user_id):
    try:
        return SystemUser.objects.get(ledger_id=email_user_id)
    except Exception as e:
        print(e)

def get_invoice_payment_status(invoice_id):
    try:
        inv_props = utils.get_invoice_properties(invoice_id)
        invoice_payment_status = inv_props['data']['invoice']['payment_status']
        return invoice_payment_status
    except Exception as e:
        logger.error(f'Error raised when getting the payment status of the invoice (invoice_id: {invoice_id}). exception: [{e}]')
        return '---'


class MyUserForLedgerAPI:
    def __init__(self, id, is_authenticated, is_superuser, is_staff):
        self.id = id
        self.is_authenticated = is_authenticated
        self.is_superuser = is_superuser
        self.is_staff = is_staff