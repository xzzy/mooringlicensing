from ledger_api_client import utils
from ledger_api_client.ledger_models import EmailUserRO
from ledger_api_client import api
from io import StringIO
import json

from mooringlicensing import settings
from mooringlicensing.components.main.decorators import basic_exception_handler


@basic_exception_handler
def retrieve_email_userro(email_user_id):
    return EmailUserRO.objects.get(id=email_user_id)


def get_invoice_payment_status(invoice_id):
    inv_props = utils.get_invoice_properties(invoice_id)
    invoice_payment_status = inv_props['data']['invoice']['payment_status']
    return invoice_payment_status


class MyUserForLedgerAPI:
    def __init__(self, id, is_authenticated, is_superuser, is_staff):
        self.id = id
        self.is_authenticated = is_authenticated
        self.is_superuser = is_superuser
        self.is_staff = is_staff
            

def update_account_details_in_ledger(request, data):
    """
    Update account details in ledger
    """
    # Create json filelike obj from the 'data' object, which is dictionary type
    test_data = json.dumps({'payload': data})  # dict --> json str
    file_like_obj = StringIO(test_data)  # json str --> json filelike obj
    # Create user object which is used in the function: update_account_details() in the ledger_api_client
    user = MyUserForLedgerAPI(request.user.id, request.user.is_authenticated, request.user.is_superuser,  request.user.is_staff)
    file_like_obj.user = user  # add user object to file_like_obj
    # Pass the filelike obj created above to the function below in order to update the personal data in the ledger.
    ret = api.update_account_details(file_like_obj, request.user.id)

    return ret
