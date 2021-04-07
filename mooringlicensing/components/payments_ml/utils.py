import logging
from datetime import datetime

import pytz
from django.http import HttpResponseRedirect
from django.urls import reverse
from ledger.checkout.utils import create_basket_session, create_checkout_session, calculate_excl_gst
from ledger.settings_base import TIME_ZONE
from rest_framework import serializers

from mooringlicensing import settings
from mooringlicensing.components.payments_ml.models import ApplicationFee, FeeConstructor

#test

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


def create_fee_lines(proposal, invoice_text=None, vouchers=[], internal=False):
    """ Create the ledger lines - line item for application fee sent to payment system """

    db_processes_after_success = {}

    # if proposal.application_type.name == ApplicationType.APIARY:
    #     line_items, db_processes_after_success = create_fee_lines_apiary(proposal)  # This function returns line items and db_processes as a tuple
    #     # line_items, db_processes_after_success = create_fee_lines_apiary(proposal)  # This function returns line items and db_processes as a tuple
    # elif proposal.application_type.name == ApplicationType.SITE_TRANSFER:
    #     line_items, db_processes_after_success = create_fee_lines_site_transfer(proposal)  # This function returns line items and db_processes as a tuple
    # else:
    now = datetime.now(pytz.timezone(TIME_ZONE))
    now_str = now.strftime('%Y-%m-%d %H:%M')
    today = now.date()

    # Retrieve FeeItem object from FeeConstructor object
    fee_constructor = FeeConstructor.get_fee_constructor_by_application_type_and_date(proposal.application_type, today)
    if not fee_constructor:
        # Fees have not been configured for this application type and date
        raise Exception('FeeConstructor object for the ApplicationType: {} not found for the date: {}'.format(proposal.application_type, today))

    # fee_item = fee_constructor.get_fee_item(proposal.proposal_type, proposal.vessel_details.vessel_length, today)
    fee_item = fee_constructor.get_fee_item(proposal.proposal_type, proposal.vessel_length, today)

    line_items = [
        {
            'ledger_description': 'Application Fee - {} - {}'.format(now_str, proposal.lodgement_number),
            # 'oracle_code': proposal.application_type.oracle_code_application,
            'oracle_code': 'aho',
            'price_incl_tax':  fee_item.amount,
            'price_excl_tax':  calculate_excl_gst(fee_item.amount) if fee_constructor.incur_gst else fee_item.amount,
            'quantity': 1,
        },
    ]

    logger.info('{}'.format(line_items))

    return line_items, db_processes_after_success


NAME_SESSION_APPLICATION_INVOICE = 'mooringlicensing_app_invoice'


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
