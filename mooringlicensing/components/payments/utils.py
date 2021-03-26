from datetime import datetime

from django.http import HttpResponseRedirect
from django.urls import reverse
from ledger.checkout.utils import create_basket_session, create_checkout_session

from mooringlicensing import settings


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
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Non 'Apiary' proposal
    # application_price = proposal.application_type.application_fee
    line_items = [
        {
            'ledger_description': 'Application Fee - {} - {}'.format(now, proposal.lodgement_number),
            # 'oracle_code': proposal.application_type.oracle_code_application,
            'oracle_code': 'aho',
            # 'price_incl_tax':  application_price,
            # 'price_excl_tax':  application_price if proposal.application_type.is_gst_exempt else calculate_excl_gst(application_price),
            'price_incl_tax':  100,
            'price_excl_tax':  100,
            'quantity': 1,
        },
    ]

    # logger.info('{}'.format(line_items))

    # return line_items, db_processes_after_success
    return line_items
