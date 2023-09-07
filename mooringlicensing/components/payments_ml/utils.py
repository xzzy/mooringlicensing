import logging
# from _pydecimal import Decimal
import decimal

import pytz
from django.http import HttpResponse
from django.urls import reverse
# from ledger.checkout.utils import create_basket_session, create_checkout_session, calculate_excl_gst, use_existing_basket_from_invoice
from ledger_api_client.utils import create_basket_session, create_checkout_session, calculate_excl_gst, use_existing_basket_from_invoice
# from ledger.settings_base import TIME_ZONE
from ledger_api_client.settings_base import *
from mooringlicensing import settings
from mooringlicensing.components.payments_ml.models import ApplicationFee, DcvPermitFee, \
    DcvAdmissionFee, StickerActionFee

#test

# logger = logging.getLogger('mooringlicensing')
logger = logging.getLogger(__name__)


def checkout(request, email_user, lines, return_url, return_preload_url, booking_reference, invoice_text=None, vouchers=[], proxy=False,):
    basket_params = {
        'products': make_serializable(lines),
        # 'products': [{'ledger_description': 'test', 'oracle_code': 'T1 EXEMPT', 'price_incl_tax': 138.0, 'price_excl_tax': 125.454545454545, 'quantity': 1}],
        'vouchers': vouchers,
        'system': settings.PAYMENT_SYSTEM_ID,
        'custom_basket': True,
        'tax_override': True,
        'booking_reference': booking_reference,
    }

    email_user_id = email_user.id if request.user.is_anonymous else request.user.id
    basket_hash = create_basket_session(request, email_user_id, basket_params)
    checkout_params = {
        'system': settings.PAYMENT_SYSTEM_ID,
        'fallback_url': request.build_absolute_uri('/'),
        'return_url': return_url,
        'return_preload_url': return_preload_url,
        'force_redirect': True,
        'invoice_text': invoice_text,  # 'Reservation for Jawaid Mushtaq from 2019-05-17 to 2019-05-19 at RIA 005'
        'basket_owner': email_user.id,
        'session_type': 'ledger_api',
    }
    # if proxy or request.user.is_anonymous():
    if proxy or request.user.is_anonymous:
        # checkout_params['basket_owner'] = email_user.id
        checkout_params['basket_owner'] = email_user.id

    create_checkout_session(request, checkout_params)

    # response = HttpResponseRedirect(reverse('checkout:index'))
    # response = HttpResponseRedirect(reverse('ledgergw-payment-details'))
    # inject the current basket into the redirect response cookies
    # or else, anonymous users will be directionless
    # response.set_cookie(
    #     settings.OSCAR_BASKET_COOKIE_OPEN, basket_hash,
    #     max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME,
    #     secure=settings.OSCAR_BASKET_COOKIE_SECURE,
    #     httponly=True,
    # )
    response = HttpResponse(
        "<script> window.location='" + reverse('ledgergw-payment-details') + "';</script> <a href='" + reverse(
            'ledgergw-payment-details'
            ) + "'> Redirecting please wait: " + reverse('ledgergw-payment-details') + "</a>"
        )

    return response




def generate_line_item(application_type, fee_amount_adjusted, fee_constructor, instance, target_datetime, v_rego_no=''):
    from mooringlicensing.components.proposals.models import WaitingListApplication

    target_datetime_str = target_datetime.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d/%m/%Y %I:%M %p')
    application_type_display = fee_constructor.application_type.description
    application_type_display = application_type_display.replace('Application', '')
    application_type_display = application_type_display.replace('fees', '')
    application_type_display = application_type_display.strip()
    vessel_rego_no = v_rego_no
    if not vessel_rego_no and instance.vessel_details and instance.vessel_details.vessel:
        vessel_rego_no = instance.vessel_details.vessel.rego_no
    if not vessel_rego_no:
        # We want to show something rather than empty string
        vessel_rego_no = 'no vessel'

    proposal_type_text = '{}'.format(instance.proposal_type.description) if hasattr(instance, 'proposal_type') else ''

    if application_type.code != WaitingListApplication.code:
        # Keep season dates on the Waiting List
        ledger_description = '{} fee ({}, {}): {} (Season: {} to {}) @{}'.format(
            application_type_display,
            proposal_type_text,
            vessel_rego_no,
            instance.lodgement_number,
            fee_constructor.fee_season.start_date.strftime('%d/%m/%Y'),
            fee_constructor.fee_season.end_date.strftime('%d/%m/%Y'),
            target_datetime_str,
        )
    else:
        ledger_description = '{} fee ({}, {}): {} @{}'.format(
            application_type_display,
            proposal_type_text,
            vessel_rego_no,
            instance.lodgement_number,
            target_datetime_str,
        )

    return {
        'ledger_description': ledger_description,
        'oracle_code': application_type.get_oracle_code_by_date(target_datetime.date()),
        'price_incl_tax': float(fee_amount_adjusted),
        'price_excl_tax': float(calculate_excl_gst(fee_amount_adjusted)) if fee_constructor.incur_gst else float(fee_amount_adjusted),
        'quantity': 1,
    }


NAME_SESSION_APPLICATION_INVOICE = 'mooringlicensing_app_invoice'
NAME_SESSION_DCV_PERMIT_INVOICE = 'mooringlicensing_dcv_permit_invoice'
NAME_SESSION_DCV_ADMISSION_INVOICE = 'mooringlicensing_dcv_admission_invoice'
NAME_SESSION_STICKER_ACTION_INVOICE = 'mooringlicensing_sticker_action_invoice'


def set_session_sticker_action_invoice(session, application_fee):
    """ Application Fee session ID """
    session[NAME_SESSION_STICKER_ACTION_INVOICE] = application_fee.id
    session.modified = True


def get_session_sticker_action_invoice(session):
    """ Application Fee session ID """
    if NAME_SESSION_STICKER_ACTION_INVOICE in session:
        application_fee_id = session[NAME_SESSION_STICKER_ACTION_INVOICE]
    else:
        raise Exception('Application not in Session')

    try:
        return StickerActionFee.objects.get(id=application_fee_id)
    except StickerActionFee.DoesNotExist:
        raise Exception('StickerActionFee not found for id: {}'.format(application_fee_id))


def delete_session_sticker_action_invoice(session):
    """ Application Fee session ID """
    if NAME_SESSION_STICKER_ACTION_INVOICE in session:
        del session[NAME_SESSION_STICKER_ACTION_INVOICE]
        session.modified = True


def set_session_application_invoice(session, application_fee):
    print('in set_session_application_invoice')

    """ Application Fee session ID """
    session[NAME_SESSION_APPLICATION_INVOICE] = application_fee.id
    session.modified = True


class ItemNotSetInSessionException(Exception):
    pass


def get_session_application_invoice(session):
    print('in get_session_application_invoice')

    """ Application Fee session ID """
    if NAME_SESSION_APPLICATION_INVOICE in session:
        application_fee_id = session[NAME_SESSION_APPLICATION_INVOICE]
    else:
        # Reach here when the ApplicationFeeSuccessView is accessed 2nd time.  Which is correct.
        raise ItemNotSetInSessionException('Application not in Session')

    try:
        return ApplicationFee.objects.get(id=application_fee_id)
    except ApplicationFee.DoesNotExist:
        raise


def delete_session_application_invoice(session):
    print('in delete_session_application_invoice')

    """ Application Fee session ID """
    if NAME_SESSION_APPLICATION_INVOICE in session:
        del session[NAME_SESSION_APPLICATION_INVOICE]
        session.modified = True


def set_session_dcv_permit_invoice(session, dcv_permit_fee):
    session[NAME_SESSION_DCV_PERMIT_INVOICE] = dcv_permit_fee.id
    session.modified = True


def get_session_dcv_permit_invoice(session):
    if NAME_SESSION_DCV_PERMIT_INVOICE in session:
        dcv_permit_fee_id = session[NAME_SESSION_DCV_PERMIT_INVOICE]
    else:
        raise Exception('DcvPermit not in Session')

    try:
        return DcvPermitFee.objects.get(id=dcv_permit_fee_id)
    except DcvPermitFee.DoesNotExist:
        raise Exception('DcvPermit not found for application {}'.format(dcv_permit_fee_id))


def delete_session_dcv_permit_invoice(session):
    if NAME_SESSION_DCV_PERMIT_INVOICE in session:
        del session[NAME_SESSION_DCV_PERMIT_INVOICE]
        session.modified = True


def set_session_dcv_admission_invoice(session, dcv_admission_fee):
    session[NAME_SESSION_DCV_ADMISSION_INVOICE] = dcv_admission_fee.id
    session.modified = True


def get_session_dcv_admission_invoice(session):
    if NAME_SESSION_DCV_ADMISSION_INVOICE in session:
        dcv_admission_fee_id = session[NAME_SESSION_DCV_ADMISSION_INVOICE]
    else:
        raise Exception('DcvAdmission not in Session')

    try:
        return DcvAdmissionFee.objects.get(id=dcv_admission_fee_id)
    except DcvAdmissionFee.DoesNotExist:
        raise Exception('DcvAdmission not found for application {}'.format(dcv_admission_fee_id))


def delete_session_dcv_admission_invoice(session):
    if NAME_SESSION_DCV_ADMISSION_INVOICE in session:
        del session[NAME_SESSION_DCV_ADMISSION_INVOICE]
        session.modified = True


def make_serializable(line_items):
    for line in line_items:
        for key in line:
            if isinstance(line[key], decimal.Decimal):
                # Convert Decimal to str
                line[key] = float(line[key])
    return line_items


def checkout_existing_invoice(request, invoice, return_url_ns='public_booking_success'):

    basket, basket_hash = use_existing_basket_from_invoice(invoice.reference)
    return_preload_url = settings.MOORING_LICENSING_EXTERNAL_URL + reverse(return_url_ns)
    checkout_params = {
        'system': settings.PAYMENT_SYSTEM_ID,
        'fallback_url': request.build_absolute_uri('/'),
        'return_url': request.build_absolute_uri(reverse(return_url_ns)),
        'return_preload_url': return_preload_url,
        'force_redirect': True,
        'invoice_text': invoice.text,
    }

    if request.user.is_anonymous():
        # We need to determine the basket owner and set it to the checkout_params to proceed the payment
        application_fee = ApplicationFee.objects.filter(invoice_reference=invoice.reference)
        if application_fee:
            application_fee = application_fee[0]
            # checkout_params['basket_owner'] = application_fee.approval.relevant_applicant_email_user.id
            checkout_params['basket_owner'] = application_fee.proposal.applicant_id
        else:
            # Should not reach here
            # At the moment, there should be only the 'annual rental fee' invoices for anonymous user
            pass

    create_checkout_session(request, checkout_params)

    # use HttpResponse instead of HttpResponseRedirect - HttpResonseRedirect does not pass cookies which is important for ledger to get the correct basket
    response = HttpResponse(
        "<script> window.location='" + reverse('checkout:index') + "';</script> <a href='" + reverse(
            'checkout:index') + "'> Redirecting please wait: " + reverse('checkout:index') + "</a>")

    # inject the current basket into the redirect response cookies
    # or else, anonymous users will be directionless
    response.set_cookie(
        settings.OSCAR_BASKET_COOKIE_OPEN, basket_hash,
        max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME,
        secure=settings.OSCAR_BASKET_COOKIE_SECURE, httponly=True
    )
    return response


def oracle_integration(date,override):
    #system = '0517'
    oracle_codes = oracle_parser(date, settings.PAYMENT_SYSTEM_ID, 'Disturbance Approval System', override=override)


