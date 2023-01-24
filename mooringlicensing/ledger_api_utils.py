from ledger_api_client.ledger_models import EmailUserRO

from mooringlicensing.components.main.decorators import basic_exception_handler


@basic_exception_handler
def retrieve_email_userro(email_user_id):
    return EmailUserRO.objects.get(id=email_user_id)
