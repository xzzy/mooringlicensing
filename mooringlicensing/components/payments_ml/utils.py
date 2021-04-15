import logging
from datetime import datetime

import pytz
from django.http import HttpResponseRedirect
from django.urls import reverse
from ledger.checkout.utils import create_basket_session, create_checkout_session, calculate_excl_gst
from ledger.settings_base import TIME_ZONE
from rest_framework import serializers

from mooringlicensing import settings
from mooringlicensing.components.approvals.models import DcvPermit
from mooringlicensing.components.main.models import ApplicationType
from mooringlicensing.components.payments_ml.models import ApplicationFee, FeeConstructor, DcvPermitFee

#test
from mooringlicensing.components.proposals.models import Proposal

logger = logging.getLogger('payment_checkout')


def checkout(request, proposal, lines, return_url_ns='public_payment_success', return_preload_url_ns='public_payment_success', invoice_text=None, vouchers=[], proxy=False):
    basket_params = {
        'products': lines,
        'vouchers': vouchers,
        'system': settings.PAYMENT_SYSTEM_ID,
        'custom_basket': True,
    }

    basket, basket_hash = create_basket_session(request, basket_params)
    #fallback_url = request.build_absolute_uri('/')
    checkout_params = {
        'system': settings.PAYMENT_SYSTEM_ID,
        'fallback_url': request.build_absolute_uri('/'),                                      # 'http://mooring-ria-jm.dbca.wa.gov.au/'
        'return_url': request.build_absolute_uri(reverse(return_url_ns)),          # 'http://mooring-ria-jm.dbca.wa.gov.au/success/'
        'return_preload_url': request.build_absolute_uri(reverse(return_url_ns)),  # 'http://mooring-ria-jm.dbca.wa.gov.au/success/'
        #'fallback_url': fallback_url,
        #'return_url': fallback_url,
        #'return_preload_url': fallback_url,
        'force_redirect': True,
        #'proxy': proxy,
        'invoice_text': invoice_text,                                                         # 'Reservation for Jawaid Mushtaq from 2019-05-17 to 2019-05-19 at RIA 005'
    }
    #    if not internal:
    #        checkout_params['check_url'] = request.build_absolute_uri('/api/booking/{}/booking_checkout_status.json'.format(booking.id))
    #if internal or request.user.is_anonymous():
    if proxy or request.user.is_anonymous():
        #checkout_params['basket_owner'] = booking.customer.id
        # checkout_params['basket_owner'] = proposal.submitter_id  # There isn't a submitter_id field... supposed to be submitter.id...?
        checkout_params['basket_owner'] = proposal.submitter.id


    create_checkout_session(request, checkout_params)

    #    if internal:
    #        response = place_order_submission(request)
    #    else:
    response = HttpResponseRedirect(reverse('checkout:index'))
    # inject the current basket into the redirect response cookies
    # or else, anonymous users will be directionless
    response.set_cookie(
        settings.OSCAR_BASKET_COOKIE_OPEN, basket_hash,
        max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME,
        secure=settings.OSCAR_BASKET_COOKIE_SECURE, httponly=True
    )

    #    if booking.cost_total < 0:
    #        response = HttpResponseRedirect('/refund-payment')
    #        response.set_cookie(
    #            settings.OSCAR_BASKET_COOKIE_OPEN, basket_hash,
    #            max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME,
    #            secure=settings.OSCAR_BASKET_COOKIE_SECURE, httponly=True
    #        )
    #
    #    # Zero booking costs
    #    if booking.cost_total < 1 and booking.cost_total > -1:
    #        response = HttpResponseRedirect('/no-payment')
    #        response.set_cookie(
    #            settings.OSCAR_BASKET_COOKIE_OPEN, basket_hash,
    #            max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME,
    #            secure=settings.OSCAR_BASKET_COOKIE_SECURE, httponly=True
    #        )

    return response


def create_fee_lines(instance, invoice_text=None, vouchers=[], internal=False):
    """ Create the ledger lines - line item for application fee sent to payment system """

    # Any changes to the DB should be made after the success of payment process
    db_processes_after_success = {}

    if isinstance(instance, Proposal):
        application_type = instance.application_type
        vessel_length = instance.vessel_details.vessel_applicable_length
        proposal_type = instance.proposal_type
    elif isinstance(instance, DcvPermit):
        application_type = ApplicationType.objects.get(code=settings.APPLICATION_TYPE_DCV_PERMIT['code'])
        vessel_length = 1
        proposal_type = None

    target_datetime = datetime.now(pytz.timezone(TIME_ZONE))
    target_date = target_datetime.date()
    target_datetime_str = target_datetime.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d/%m/%Y %I:%M %p')

    # Retrieve FeeItem object from FeeConstructor object
    fee_constructor = FeeConstructor.get_current_fee_constructor_by_application_type_and_date(application_type, target_date)
    if not fee_constructor:
        # Fees have not been configured for this application type and date
        raise Exception('FeeConstructor object for the ApplicationType: {} not found for the date: {}'.format(application_type, target_date))
    db_processes_after_success['fee_constructor_id'] = fee_constructor.id
    db_processes_after_success['season_start_date'] = fee_constructor.fee_season.start_date.__str__()
    db_processes_after_success['season_end_date'] = fee_constructor.fee_season.end_date.__str__()
    db_processes_after_success['datetime_for_calculating_fee'] = target_datetime.__str__()

    fee_item = fee_constructor.get_fee_item(vessel_length, proposal_type, target_date)

    line_items = [
        {
            'ledger_description': '{} Fee: {} - {}'.format(application_type.description,  instance.lodgement_number, target_datetime_str),
            'oracle_code': application_type.oracle_code,
            'price_incl_tax':  fee_item.amount,
            'price_excl_tax':  calculate_excl_gst(fee_item.amount) if fee_constructor.incur_gst else fee_item.amount,
            'quantity': 1,
        },
    ]

    logger.info('{}'.format(line_items))

    return line_items, db_processes_after_success


NAME_SESSION_APPLICATION_INVOICE = 'mooringlicensing_app_invoice'
NAME_SESSION_DCV_PERMIT_INVOICE = 'mooringlicensing_dcv_permit_invoice'


def set_session_application_invoice(session, application_fee):
    print('in set_session_application_invoice')

    """ Application Fee session ID """
    session[NAME_SESSION_APPLICATION_INVOICE] = application_fee.id
    session.modified = True


def get_session_application_invoice(session):
    print('in get_session_application_invoice')

    """ Application Fee session ID """
    if NAME_SESSION_APPLICATION_INVOICE in session:
        application_fee_id = session[NAME_SESSION_APPLICATION_INVOICE]
    else:
        raise Exception('Application not in Session')

    try:
        return ApplicationFee.objects.get(id=application_fee_id)
    except ApplicationFee.DoesNotExist:
        raise Exception('Application not found for application {}'.format(application_fee_id))


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
        raise Exception('Application not found for application {}'.format(dcv_permit_fee_id))


def delete_session_dcv_permit_invoice(session):
    if NAME_SESSION_DCV_PERMIT_INVOICE in session:
        del session[NAME_SESSION_DCV_PERMIT_INVOICE]
        session.modified = True
