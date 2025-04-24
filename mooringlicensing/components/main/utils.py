import os
from io import BytesIO

from ledger_api_client.settings_base import TIME_ZONE
from django.utils import timezone
from confy import env
import re

import requests
from requests.auth import HTTPBasicAuth
import json
import pytz
from django.conf import settings
from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import Q
from mooringlicensing.components.approvals.models import (
    Sticker, AnnualAdmissionPermit, AuthorisedUserPermit, DcvPermitDocument,
    MooringLicence, Approval, WaitingListAllocation, ApprovalHistory, DcvPermit, Approval
)
from mooringlicensing.components.proposals.email import send_sticker_printing_batch_email
from mooringlicensing.components.proposals.models import (
    MooringBay,
    Mooring,
    StickerPrintingBatch,
    Proposal,
)
from rest_framework import serializers
from openpyxl import Workbook
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


def is_payment_officer(user):
    from mooringlicensing.helpers import belongs_to
    return user.is_authenticated and (belongs_to(user, settings.GROUP_MOORING_LICENSING_PAYMENT_OFFICER) or user.is_superuser)


def to_local_tz(_date):
    local_tz = pytz.timezone(settings.TIME_ZONE)
    return _date.astimezone(local_tz)


def check_db_connection():
    """  check connection to DB exists, connect if no connection exists """
    try:
        if not connection.is_usable():
            connection.connect()
    except Exception as e:
        connection.connect()

def get_bookings(booking_date, rego_no=None, mooring_id=None):
    url = settings.MOORING_BOOKINGS_API_URL + "bookings/" + settings.MOORING_BOOKINGS_API_KEY + '/' 
    myobj = {
            'date': booking_date,
            }
    if rego_no:
        myobj.update({'rego_no': rego_no})
    if mooring_id:
        myobj.update({'mooring_id': mooring_id})
    try:
        res = requests.post(url, data=myobj)
        res.raise_for_status()
        data = res.json().get('data')
        updated_data = []
        # phone number
        for booking in data:
            customer_phone_number = ''
            if booking.get("booking_phone_number"):
                customer_phone_number = booking.get("booking_phone_number")
            elif booking.get("customer_account_phone_number"):
                customer_phone_number = booking.get("customer_account_phone_number")
            booking.update({"customer_phone_number": customer_phone_number})
            updated_data.append(booking)
        return updated_data
    except Exception as e:
        logger.error(f'Error raised while getting bookings. Error: [{e}]')
        return []

def import_mooring_bookings_data():
    errors = []
    updates = []
    parks_errors, parks_updates = retrieve_marine_parks()
    mooring_errors, mooring_updates = retrieve_mooring_areas()
    errors.extend(parks_errors)
    errors.extend(mooring_errors)
    updates.extend(parks_updates)
    updates.extend(mooring_updates)
    return errors, updates

def validate_files(approvals):
    #check if a record file exists or not - if it doesn't then update the table row to reflect that
    if len(approvals) > 0:

        #check if private-media dir exists, if not all pdf files need to be generated    
        private_media_location = settings.PRIVATE_MEDIA_STORAGE_LOCATION
        if not os.path.exists(private_media_location):
            return approvals

        missing_doc_ids = []
        if isinstance(approvals[0], DcvPermit):
            #check dcv dir exists
            if not os.path.exists(os.path.join(private_media_location,'dcv_permit')):
                return approvals

            dcv_with_file_ids = DcvPermitDocument.objects.distinct('dcv_permit_id').values_list("dcv_permit_id",flat=True)
            no_files = list(approvals.exclude(id__in=dcv_with_file_ids).values_list('id', flat=True)) #we will keep these for later
            check_files = approvals.filter(id__in=dcv_with_file_ids) #we will check if the specified files actually exist

            for i in check_files:
                if not os.path.exists(os.path.join(private_media_location,'dcv_permit/{}'.format(i.id))):
                    missing_doc_ids.append(i.id)
            DcvPermitDocument.objects.filter(dcv_permit_id__in=missing_doc_ids).delete()
            generate_pdf_ids = no_files + missing_doc_ids
            return DcvPermit.objects.filter(id__in=generate_pdf_ids)
        else:
            approval_class = approvals[0].__class__
            #check proposal dir exists
            if not os.path.exists(os.path.join(private_media_location,'proposal')):
                return approvals

            no_files = list(approvals.filter(licence_document=None).values_list('id', flat=True)) #we will keep these for later
            check_files = approvals.exclude(licence_document=None) #we will check if the specified files actually exist  

            for i in check_files:
                if not os.path.exists(os.path.join(private_media_location,'proposal/{}/approval_documents'.format(i.current_proposal.id))):
                    missing_doc_ids.append(i.id)
            Approval.objects.filter(id__in=missing_doc_ids).update(licence_document=None)
            generate_pdf_ids = no_files + missing_doc_ids
            return approval_class.objects.filter(id__in=generate_pdf_ids)

    return approvals

def create_pdf_licence(approvals):
    if len(approvals) > 0:
        permit_name = approvals[0].__class__.__name__

        errors = []
        updates = []

        for idx, a in enumerate(approvals):
            try:
                if isinstance(a, DcvPermit) and len(a.dcv_permit_documents.all())==0:
                    a.generate_dcv_permit_doc()
                elif not hasattr(a, 'licence_document') or a.licence_document is None: 
                    a.generate_doc()
                print(f'{idx}, Created PDF for {permit_name}: {a}')
                updates.append(a.lodgement_number)
            except Exception as e:
                errors.append(e)

        return errors, updates
    else:
        return [],[]

def generate_pdf_files():

    errors = []
    updates = []

    ml_qs = MooringLicence.objects.filter(Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_APPROVED)|Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_PRINTING_STICKER))
    ml_qs = validate_files(ml_qs)
    ml_e,ml_u = create_pdf_licence(ml_qs)
    errors.append(ml_e)
    updates.append(ml_u)

    aap_qs = AnnualAdmissionPermit.objects.filter(Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_APPROVED)|Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_PRINTING_STICKER))
    aap_qs = validate_files(aap_qs)
    aap_e,aap_u = create_pdf_licence(aap_qs)
    errors.append(aap_e)
    updates.append(aap_u)

    aup_qs = AuthorisedUserPermit.objects.filter(Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_APPROVED)|Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_PRINTING_STICKER))
    aup_qs = validate_files(aup_qs)
    aup_e,aup_u = create_pdf_licence(aup_qs)
    errors.append(aup_e)
    updates.append(aup_u)

    wla_qs = WaitingListAllocation.objects.filter(Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_APPROVED)|Q(current_proposal__processing_status=Proposal.PROCESSING_STATUS_PRINTING_STICKER))
    wla_qs = validate_files(wla_qs)
    wla_e,wla_u = create_pdf_licence(wla_qs)
    errors.append(wla_e)
    updates.append(wla_u)

    dcv_qs = DcvPermit.objects.filter(status=DcvPermit.DCV_PERMIT_STATUS_CURRENT)
    dcv_qs = validate_files(dcv_qs)
    dcv_e,dcv_u = create_pdf_licence(dcv_qs)
    errors.append(dcv_e)
    updates.append(dcv_u)

    return errors, updates

## Mooring Bookings API interactions
def retrieve_mooring_areas():
    records_updated = []
    try:
        url = settings.MOORING_BOOKINGS_API_URL + "all-mooring/" + settings.MOORING_BOOKINGS_API_KEY
        res = requests.get(url)
        res.raise_for_status()
        data = res.json().get('data')
        # update Mooring records
        with transaction.atomic():
            for mooring in data:
                # get mooring_group_id from MB admin Mooring Groups, Rottnest Is Auth and store as env var
                if not env('MOORING_GROUP_ID'):
                    raise Exception('You must set MOORING_GROUP_ID env var')
                else:
                    mooring_group_id = env('MOORING_GROUP_ID')

                if mooring.get('mooring_specification') != 2 or mooring_group_id not in mooring.get('mooring_group'):
                    continue
                mooring_qs = Mooring.objects.filter(mooring_bookings_id=mooring.get("id"))
                if mooring_qs.count() > 0:
                    mo = mooring_qs[0]
                    orig_mo = deepcopy(mo)
                    mo.mooring_bookings_id=mooring.get("id")
                    mo.name=mooring.get("name")
                    try:
                        mo.mooring_bay = MooringBay.objects.get(
                            mooring_bookings_id=mooring.get('marine_park_id'), 
                            active=True
                        )
                    except:
                        continue
                    mo.vessel_size_limit = mooring.get('vessel_size_limit')
                    mo.vessel_draft_limit = mooring.get('vessel_draft_limit')
                    mo.vessel_beam_limit = mooring.get('vessel_beam_limit')
                    mo.vessel_weight_limit = mooring.get('vessel_weight_limit')
                    mo.mooring_bookings_mooring_specification = mooring.get('mooring_specification')
                    mo.mooring_bookings_bay_id = mooring.get('marine_park_id')
                    mo.save()
                    
                    if (float(mo.vessel_size_limit) != float(orig_mo.vessel_size_limit) or
                        float(mo.vessel_draft_limit) != float(orig_mo.vessel_draft_limit) or
                        float(mo.vessel_beam_limit) != float(orig_mo.vessel_beam_limit) or
                        float(mo.vessel_weight_limit) != float(orig_mo.vessel_weight_limit) or
                        float(mo.mooring_bookings_mooring_specification) != float(orig_mo.mooring_bookings_mooring_specification) or
                        float(mo.mooring_bookings_bay_id) != float(orig_mo.mooring_bookings_bay_id)):
                        records_updated.append(str(mo.name))
                else:
                    try:
                        mooring_bay = MooringBay.objects.get(
                            mooring_bookings_id=mooring.get('marine_park_id'), 
                            active=True
                        )
                    except:
                        continue
                    
                    mooring = Mooring.objects.create(
                            mooring_bookings_id=mooring.get("id"), 
                            name=mooring.get("name"),
                            mooring_bay = mooring_bay,
                            vessel_size_limit = mooring.get('vessel_size_limit'),
                            vessel_draft_limit = mooring.get('vessel_draft_limit'),
                            vessel_beam_limit = mooring.get('vessel_beam_limit'),
                            vessel_weight_limit = mooring.get('vessel_weight_limit'),
                            mooring_bookings_mooring_specification = mooring.get('mooring_specification'),
                            mooring_bookings_bay_id = mooring.get('marine_park_id')
                            )
                    logger.info("Mooring created: {}".format(str(mooring)))
                    records_updated.append(str(mooring.name))

            logger.info("Moorings updated: {}".format(str(records_updated)))
            # update active status of any MooringBay records not found in api data
            for mooring_obj in Mooring.objects.all():
                if mooring_obj.mooring_bookings_id not in [x.get("id") for x in data]:
                    mooring_obj.active = False
                    mooring_obj.save()
                elif mooring_obj.mooring_bookings_id in [x.get("id") for x in data]:
                    mooring_obj.active = True
                    mooring_obj.save()
            return [], records_updated

    except Exception as e:
        logger.error('retrieve_mooring_areas() error', exc_info=True)
        # email only prints len() of error list
        return ['check log',], records_updated

def retrieve_marine_parks():
    records_updated = []
    try:
        # CRON (every night?)  Plus management button for manual control.
        url = settings.MOORING_BOOKINGS_API_URL + "marine-parks/" + settings.MOORING_BOOKINGS_API_KEY
        res = requests.get(url)
        res.raise_for_status()
        data = res.json().get('data')
        # update MooringBay records
        with transaction.atomic():
            for bay in data:
                # get mooring_group_id from MB admin Mooring Groups, Rottnest Is Auth and store as env var
                if not env('MOORING_GROUP_ID'):
                    raise Exception('You must set MOORING_GROUP_ID env var')
                else:
                    mooring_group_id = env('MOORING_GROUP_ID')

                if mooring_group_id != bay.get('mooring_group'):
                    continue
                mooring_bay_qs = MooringBay.objects.filter(mooring_bookings_id=bay.get("id"))
                if mooring_bay_qs.count() > 0:
                    mb = mooring_bay_qs[0]
                    if mb.name != bay.get("name"):
                        mb.name=bay.get("name")
                        mb.save()
                        records_updated.append(str(mb.name))
                else:
                    mooring_bay = MooringBay.objects.create(mooring_bookings_id=bay.get("id"), name=bay.get("name"))
                    logger.info("Mooring Bay created: {}".format(str(mooring_bay)))
                    records_updated.append(str(mooring_bay.name))

            # update active status of any MooringBay records not found in api data
            for mooring_bay in MooringBay.objects.all():
                if mooring_bay.mooring_bookings_id not in [x.get("id") for x in data]:
                    mooring_bay.active = False
                    mooring_bay.save()
            return [], records_updated
    except Exception as e:
        logger.error('retrieve_marine_parks() error', exc_info=True)
        return ['check log',], records_updated

def handle_validation_error(e):
    if hasattr(e, 'error_dict'):
        raise serializers.ValidationError(repr(e.error_dict))
    else:
        if hasattr(e, 'message'):
            raise serializers.ValidationError(e.message)
        else:
            raise


def sticker_export():
    """
    This function exports sticker details data as a spreadsheet file,
    and store it as a StickerPrintingBatch object.
    """
    logger = logging.getLogger('cron_tasks')

    stickers = Sticker.objects.filter(
        sticker_printing_batch__isnull=True,
        status=Sticker.STICKER_STATUS_READY,
    )

    errors = []
    updates = []
    today = timezone.localtime(timezone.now()).date()

    if stickers.count():
        try:
            wb = Workbook()
            virtual_workbook = BytesIO()
            ws1 = wb.create_sheet(title="Info", index=0)

            ws1.append([
                'Date',
                'First Name',
                'Last Name',
                'Address Line 1',
                'Address Line 2',
                'Suburb',
                'State',
                'Postcode',
                'Sticker Type',
                'Sticker Number',
                'Vessel Registration Number',
                'Moorings',
                'Length Colour',
                'White info',
            ])
            for sticker in stickers:
                try:
                    # Sticker is being printed.  We assign a new number here.
                    sticker.number = '{0:07d}'.format(sticker.next_number)
                    sticker.save()

                    moorings = sticker.get_moorings()
                    mooring_names = [mooring.name for mooring in moorings]
                    mooring_names = ', '.join(mooring_names)

                    if not sticker.postal_address_line1 or not sticker.postal_address_locality or not sticker.postal_address_state or not sticker.postal_address_postcode:
                        logger.warning(f'Postal address not found for the Sticker: [{sticker}].')
                        continue

                    ws1.append([
                        today.strftime('%d/%m/%Y'),
                        sticker.first_name,
                        sticker.last_name,
                        sticker.postal_address_line1,
                        sticker.postal_address_line2,
                        sticker.postal_address_locality.upper(),
                        sticker.postal_address_state.upper(),
                        sticker.postal_address_postcode,
                        sticker.approval.description,
                        sticker.number,
                        sticker.vessel_registration_number.upper(),
                        mooring_names,
                        sticker.get_sticker_colour(),
                        sticker.get_white_info(),
                    ])
                    logger.info('Sticker: {} details added to the spreadsheet'.format(sticker.number))
                    updates.append(sticker.number)

                    new_approval_history_entry = ApprovalHistory.objects.create(
                        vessel_ownership=sticker.approval.current_proposal.vessel_ownership,
                        approval=sticker.approval,
                        proposal=sticker.approval.current_proposal,
                        start_date=sticker.approval.issue_date,
                        approval_letter=sticker.approval.licence_document,
                    )
                    new_approval_history_entry.stickers.add(sticker)
                    new_approval_history_entry.save()

                except Exception as e:
                    err_msg = 'Error adding sticker: {} details to spreadsheet.'.format(sticker.number)
                    logger.error('{}\n{}'.format(err_msg, str(e)))
                    errors.append(err_msg)

            wb.save(virtual_workbook)

            batch_obj = StickerPrintingBatch.objects.create()
            filename = 'RIA-{}.xlsx'.format(batch_obj.uploaded_date.astimezone(pytz.timezone(TIME_ZONE)).strftime('%Y%m%d'))
            batch_obj._file.save(filename, virtual_workbook, save=False)
            batch_obj.name = filename
            batch_obj.save()
            logger.info('Sticker printing batch file {} generated successfully.'.format(batch_obj.name))

            # Update sticker objects
            stickers.update(
                sticker_printing_batch=batch_obj,  # Keep status 'printing' because we still have to wait for the sticker printed.
            )
        except Exception as e:
            err_msg = 'Error generating the sticker printing batch spreadsheet file for the stickers: {}'.format(', '.join([sticker.number for sticker in stickers]))
            logger.error('{}\n{}'.format(err_msg, str(e)))
            errors.append(err_msg)
    return updates, errors


def email_stickers_document():
    """
    Email the file generated at the sticker_export() function to the sticker company:
    """
    logger = logging.getLogger('cron_tasks')
    updates, errors = [], []

    try:
        batches = StickerPrintingBatch.objects.filter(emailed_datetime__isnull=True)
        if batches.count():
            current_datetime = timezone.localtime(timezone.now())

            # Send sticker details spreadsheet file to the printing company
            send_sticker_printing_batch_email(batches)

            for batch in batches:
                batch.emailed_datetime = current_datetime
                batch.save()
                updates.append(batch.name)

                # Update sticker status
                stickers = Sticker.objects.filter(sticker_printing_batch=batch)
                for sticker in stickers:
                    sticker.status = Sticker.STICKER_STATUS_AWAITING_PRINTING
                    sticker.save()
                    logger.info(f'Status: [{Sticker.STICKER_STATUS_AWAITING_PRINTING}] has been set to the sticker: [{sticker}]')
                    if sticker.sticker_to_replace:
                        # new sticker has the old sticker here if it's created for renewal
                        # When this sticker is created for renewal, set 'expired' status to the old sticker.
                        sticker.sticker_to_replace.status = Sticker.STICKER_STATUS_EXPIRED
                        sticker.sticker_to_replace.save()
                        logger.info(f'Status: [{Sticker.STICKER_STATUS_EXPIRED}] has been set to the sticker: [{sticker.sticker_to_replace}]')

    except Exception as e:
        err_msg = 'Error sending the sticker printing batch spreadsheet file(s): {}'.format(', '.join([batch.name for batch in batches]))
        logger.error('{}\n{}'.format(err_msg, str(e)))
        errors.append(err_msg)

    return updates, errors


## DoT vessel rego check
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_dot_vessel_information(request,json_string):
    DOT_URL=settings.DOT_URL
    paramGET=json_string.replace("\n", "")
    client_ip = get_client_ip(request)
    auth=auth=HTTPBasicAuth(settings.DOT_USERNAME,settings.DOT_PASSWORD)
    r = requests.get(DOT_URL+"?paramGET="+paramGET+"&client_ip="+client_ip, auth=auth)
    return r.text

def export_to_mooring_booking(approval_id):
    try:
        url = settings.MOORING_BOOKINGS_API_URL + "licence-create-update/" + settings.MOORING_BOOKINGS_API_KEY + '/' 
        approval = Approval.objects.get(id=approval_id)
        status = 'active' if approval.status == 'current' else 'cancelled'
        licence_type = None
        if type(approval.child_obj) == MooringLicence:
            licence_type = 1
        elif type(approval.child_obj) == AuthorisedUserPermit:
            licence_type = 2
        elif type(approval.child_obj) == AnnualAdmissionPermit:
            licence_type = 3
        errors = []
        updates = []
        if approval and type(approval.child_obj) in [AnnualAdmissionPermit, AuthorisedUserPermit]:
            myobj = {
                    'vessel_rego': approval.current_proposal.vessel_ownership.vessel.rego_no,
                    'licence_id': approval.id,
                    'licence_type': licence_type,
                    'start_date': approval.start_date.strftime('%Y-%m-%d') if approval.start_date else '',
                    'expiry_date' : approval.expiry_date.strftime('%Y-%m-%d') if approval.expiry_date else '',
                    'status' : status,
                    }
            resp = requests.post(url, data = myobj)
            if not resp or not resp.text:
                print("Server unavailable")
                raise Exception("Server unavailable")
            resp_dict = json.loads(resp.text)

            if resp_dict.get("status") == 200:
                updates.append('approval_id: {}, vessel_id: {}'.format(approval.id, approval.current_proposal.vessel_ownership.vessel.id))
                approval.export_to_mooring_booking = False
                approval.save()
            else:
                errors.append('approval_id: {}, vessel_id: {}, error_message: {}'.format(approval.id, approval.current_proposal.vessel_ownership.vessel.id, resp.text))
        elif approval and type(approval.child_obj) == MooringLicence:
            for vessel_ownership in approval.child_obj.vessel_ownership_list:
                myobj = {
                        'vessel_rego': vessel_ownership.vessel.rego_no,
                        'licence_id': approval.id,
                        'licence_type': licence_type,
                        'start_date': approval.start_date.strftime('%Y-%m-%d') if approval.start_date else '',
                        'expiry_date' : approval.expiry_date.strftime('%Y-%m-%d') if approval.expiry_date else '',
                        'status' : status,
                        }
                resp = requests.post(url, data = myobj)
                if not resp or not resp.text:
                    print("Server unavailable")
                    raise Exception("Server unavailable")
                resp_dict = json.loads(resp.text)

                if resp_dict.get("status") == 200:
                    updates.append('approval_id: {}, vessel_id: {}'.format(approval.id, vessel_ownership.vessel.id))
                else:
                    errors.append('approval_id: {}, vessel_id: {}, error_message: {}'.format(approval.id, vessel_ownership.vessel.id, resp.text))
            # do not mark mooring licences without vessels as exported
            if not errors and approval.child_obj.vessel_ownership_list:
                approval.export_to_mooring_booking = False
                approval.save()
        return errors, updates
    except Exception as e:
        print(str(e))
        logger.error(str(e))
        raise e


def calculate_minimum_max_length(fee_items_interested, max_amount_paid):
    """
    Find out MINIMUM max-length from fee_items_interested by max_amount_paid
    """
    max_length = 0
    for fee_item in fee_items_interested:
        if fee_item.incremental_amount:
            smallest_vessel_size = float(fee_item.vessel_size_category.start_size)

            larger_category = fee_item.vessel_size_category.vessel_size_category_group.get_one_larger_category(
                fee_item.vessel_size_category
            )
            if larger_category:
                max_number_of_increment = round(
                    larger_category.start_size - fee_item.vessel_size_category.start_size
                )
            else:
                max_number_of_increment = 1000  # We probably would like to cap the number of increments

            increment = 0.0
            while increment <= max_number_of_increment:
                test_vessel_size = smallest_vessel_size + increment
                fee_amount_to_pay = fee_item.get_absolute_amount(test_vessel_size)
                if fee_amount_to_pay <= max_amount_paid:
                    if not max_length or test_vessel_size > max_length:
                        max_length = test_vessel_size
                increment += 1
        else:
            fee_amount_to_pay = fee_item.get_absolute_amount()
            if fee_amount_to_pay <= max_amount_paid:
                # Find out start size of one larger category
                larger_category = fee_item.vessel_size_category.vessel_size_category_group.get_one_larger_category(
                    fee_item.vessel_size_category
                )
                if larger_category:
                    if not max_length or larger_category.start_size > max_length:
                        if larger_category.include_start_size:
                            max_length = float(larger_category.start_size) - 0.00001
                        else:
                            max_length = float(larger_category.start_size)
                else:
                    max_length = None
            else:
                # The amount to pay is now more than the max amount paid
                # Assuming larger vessel is more expensive, the all the fee_items left are more expensive than max_amount_paid
                break
    return max_length


def calculate_max_length(fee_constructor, max_amount_paid, proposal_type):
    # All the amendment FeeItems interested
    # Ordered by 'start_size' ascending order, which means the cheapest fee_item first.
    fee_items_interested = fee_constructor.feeitem_set.filter(proposal_type=proposal_type).order_by('vessel_size_category__start_size')
    max_length = calculate_minimum_max_length(fee_items_interested, max_amount_paid)
    return max_length


def reorder_wla(target_bay):
    logger.info(f'Ordering WLAs for the bay: [{target_bay}]...')
    place = 1
    # set wla order per bay for current allocations
    for w in WaitingListAllocation.objects.filter(
        wla_queue_date__isnull=False,
        current_proposal__preferred_bay=target_bay,
        status__in=[
            Approval.APPROVAL_STATUS_CURRENT,
            Approval.APPROVAL_STATUS_SUSPENDED,
        ],
        internal_status__in=[
            Approval.INTERNAL_STATUS_WAITING,
        ]
    ).order_by('wla_queue_date'):
        w.wla_order = place
        w.save()
        logger.info(f'Allocation order: [{w.wla_order}] has been set to the WaitingListAllocation: [{w}].')
        place += 1

def remove_html_tags(text):

    if text is None:
        return None

    HTML_TAGS_WRAPPED = re.compile(r'<[^>]+>.+</[^>]+>')
    HTML_TAGS_NO_WRAPPED = re.compile(r'<[^>]+>')

    text = HTML_TAGS_WRAPPED.sub('', text)
    text = HTML_TAGS_NO_WRAPPED.sub('', text)
    return text

def remove_script_tags(text):

    if text is None:
        return None

    SCRIPT_TAGS_WRAPPED = re.compile(r'(?i)<script[^>]+>.+</script[^>]+>')
    SCRIPT_TAGS_NO_WRAPPED = re.compile(r'(?i)<script[^>]+>')

    text = SCRIPT_TAGS_WRAPPED.sub('', text)
    text = SCRIPT_TAGS_NO_WRAPPED.sub('', text)

    ATTR_BLACKLIST = ['onresize','onvolumechange','onsuspend','onpopstate','onbeforeunload','oncontextmenu',
        'ondragstart','oncuechange','onselect','onafterprint','onmouseover','ondragleave','onstorage',
        'onbeforeprint','onhashchange','onabort','ondragover','onwaiting','onclick','onmousemove','onkeyup',
        'onmousedown','ononline','onsearch','onprogress','onfocus','onmouseup','onplaying','onstalled','oninvalid',
        'ontimeupdate','onkeypress','onseeked','onreset','onwheel','onemptied','oninput','onpagehide','onpause',
        'onloadeddata','onseeking','onunload','onpageshow','onerror','ondrop','oncanplay','oncopy','onended','oncut',
        'onsubmit','ondrag','onblur','ondragend','onplay','onratechange','onloadedmetadata','oncanplaythrough',
        'ondurationchange','onchange','ondblclick','onmousewheel','onpaste','onload','onscroll','onkeydown',
        'ontoggle','onmouseout','onoffline','onloadstart','ondragenter']
    ATTR_BLACKLIST_STR=('|').join(ATTR_BLACKLIST)

    HTML_TAGS_WITH_ATTR_WRAPPED = re.compile(r'(?i)<[^>]+('+ATTR_BLACKLIST_STR+')[\s]*=[^>]+>.+</[^>]+>')
    HTML_TAGS_WITH_ATTR_NO_WRAPPED = re.compile(r'(?i)<[^>]+('+ATTR_BLACKLIST_STR+')[\s]*=[^>]+>')

    text = HTML_TAGS_WITH_ATTR_WRAPPED.sub('', text)
    text = HTML_TAGS_WITH_ATTR_NO_WRAPPED.sub('', text)

    return text

def is_json(value):
    try:
        json.loads(value)
    except:
        return False
    return True

def sanitise_fields(instance, exclude=[], error_on_change=[]):
    if hasattr(instance,"__dict__"):
        for i in instance.__dict__:
            #remove html tags for all string fields not in the exclude list
            if not i in exclude and (isinstance(instance.__dict__[i], dict)):
                instance.__dict__[i] = sanitise_fields(instance.__dict__[i])
            
            elif isinstance(instance.__dict__[i], list) and not i in exclude:
                for j in range(0, len(instance.__dict__[i])):
                    check = instance.__dict__[i][j]
                    if isinstance(instance.__dict__[i][j],str):
                        instance.__dict__[i][j] = remove_html_tags(instance.__dict__[i][j])
                    elif isinstance(instance.__dict__[i][j], list) or isinstance(instance.__dict__[i][j], dict):
                        instance.__dict__[i][j] = sanitise_fields(instance.__dict__[i][j])
                    if i in error_on_change and check != instance.__dict__[i][j]:
                        raise serializers.ValidationError("html tags included in field")
            
            elif isinstance(instance.__dict__[i], str) and not i in exclude:
                check = instance.__dict__[i]
                setattr(instance, i, remove_html_tags(instance.__dict__[i]))
                if i in error_on_change and check != instance.__dict__[i]:
                    #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                    raise serializers.ValidationError("html tags included in field")
            elif isinstance(instance.__dict__[i], str) and i in exclude:
                #even though excluded, we still check to remove script tags
                setattr(instance, i, remove_script_tags(instance.__dict__[i]))
                if i in error_on_change and check != instance.__dict__[i]:
                    #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                    raise serializers.ValidationError("script tags included in field")
            elif (isinstance(instance.__dict__[i], list) or isinstance(instance.__dict__[i], dict)) and i in exclude:
                #if we have reached this point, it means we have a json object with fields that are allowed to contain tags
                #we'll use . notation to identify sub fields that should be carried over to the exclude and error on change lists
                #NOTE: to allow sub fields to be sanitised, the parent field should be included in both lists required for their respective children
                sub_exclude_list = list(filter(lambda e:e.startswith(i+"."), exclude))
                exclude_list = list(map(lambda e:e.replace(i+".","",1), sub_exclude_list))
                #NOTE: a sub error on change list will require the parent field to be in the exclude list, to reach this point (but not necessarily in the error_on_change list)
                sub_error_on_change_list = list(filter(lambda e:e.startswith(i+"."), error_on_change))
                error_on_change_list = list(map(lambda e:e.replace(i+".","",1), sub_error_on_change_list))

                if isinstance(instance.__dict__[i], dict):
                    check = instance.__dict__[i]
                    instance.__dict__[i] = sanitise_fields(instance.__dict__[i], exclude=exclude_list, error_on_change=error_on_change_list)
                    if i in error_on_change and check != instance.__dict__[i]:
                        raise serializers.ValidationError("html tags included in field")
                elif isinstance(instance.__dict__[i], list):
                    for j in range(0, len(instance.__dict__[i])):
                        check = instance.__dict__[i][j]
                        if isinstance(instance.__dict__[i][j],str):
                            #strings in an excluded list will be treated as excluded
                            instance.__dict__[i][j] = remove_script_tags(instance.__dict__[i][j])
                        elif isinstance(instance.__dict__[i][j], list) or isinstance(instance.__dict__[i][j], dict):
                            instance.__dict__[i][j] = sanitise_fields(instance.__dict__[i][j], exclude=exclude_list, error_on_change=error_on_change_list)
                        if i in error_on_change and check != instance.__dict__[i][j]:
                            raise serializers.ValidationError("html tags included in field")
    else:
        remove_keys = []
        for i in instance:
            #for dicts we also check the keys - they are removed completely if not sanitary (should not change keys)
            original_key = i
            if isinstance(original_key, str):
                sanitised_key = remove_html_tags(i)
                if original_key != sanitised_key:
                    remove_keys.append(original_key)
                    continue

            #remove html tags for all string fields not in the exclude list
            if not i in exclude and (isinstance(instance[i], dict)):
                instance[i] = sanitise_fields(instance[i])

            elif isinstance(instance[i], list) and not i in exclude:
                for j in range(0, len(instance[i])):
                    check = instance[i][j]
                    if isinstance(instance[i][j],str):
                        instance[i][j] = remove_html_tags(instance[i][j])
                    elif isinstance(instance[i][j], list) or isinstance(instance[i][j], dict):
                        instance[i][j] = sanitise_fields(instance[i][j])
                    if i in error_on_change and check != instance[i][j]:
                        raise serializers.ValidationError("html tags included in field")

            else:
                if isinstance(instance[i], str) and not i in exclude:
                    check = instance[i]
                    instance[i] = remove_html_tags(instance[i])
                    if i in error_on_change and check != instance[i]:
                        #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                        raise serializers.ValidationError("html tags included in field")
                elif isinstance(instance[i], str) and i in exclude:
                    #even though excluded, we still check to remove script tags
                    instance[i] = remove_script_tags(instance[i])
                    if i in error_on_change and check != instance[i]:
                        #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                        raise serializers.ValidationError("script tags included in field")
                elif (isinstance(instance[i], list) or isinstance(instance[i], dict)) and i in exclude:
                    #if we have reached this point, it means we have a json object with fields that are allowed to contain tags
                    #we'll use . notation to identify sub fields that should be carried over to the exclude and error on change lists
                    #NOTE: to allow sub fields to be sanitised, the parent field should be included in both lists required for their respective children
                    sub_exclude_list = list(filter(lambda e:e.startswith(i+"."), exclude))
                    exclude_list = list(map(lambda e:e.replace(i+".","",1), sub_exclude_list))
                    #NOTE: a sub error on change list will require the parent field to be in the exclude list, to reach this point (but not necessarily in the error_on_change list)
                    sub_error_on_change_list = list(filter(lambda e:e.startswith(i+"."), error_on_change))
                    error_on_change_list = list(map(lambda e:e.replace(i+".","",1), sub_error_on_change_list))

                    if isinstance(instance[i], dict):
                        check = instance[i]
                        instance[i] = sanitise_fields(instance[i], exclude=exclude_list, error_on_change=error_on_change_list)
                        if i in error_on_change and check != instance[i]:
                            raise serializers.ValidationError("script tags included in field")
                    elif isinstance(instance[i], list):                        
                        for j in range(0, len(instance[i])):
                            check = instance[i][j]
                            if isinstance(instance[i][j],str):
                                #strings in an excluded list will be treated as excluded
                                instance[i][j] = remove_script_tags(instance[i][j])
                            elif isinstance(instance[i][j], list) or isinstance(instance[i][j], dict):
                                instance[i][j] = sanitise_fields(instance[i][j], exclude=exclude_list, error_on_change=error_on_change_list)
                            if i in error_on_change and check != instance[i][j]:
                                raise serializers.ValidationError("script tags included in field")
                    
        for i in remove_keys:
            del instance[i]
    return instance

def file_extension_valid(file, whitelist, model):
    _, extension = os.path.splitext(file)
    extension = extension.replace(".", "").lower()

    check = whitelist.filter(name=extension).filter(
        Q(model="all") | Q(model__iexact=model)
    )
    valid = check.exists()

    return valid

def check_file(file, model_name):
    from mooringlicensing.components.main.models import FileExtensionWhitelist

    # check if extension in whitelist
    cache_key = settings.CACHE_KEY_FILE_EXTENSION_WHITELIST
    whitelist = cache.get(cache_key)
    if whitelist is None:
        whitelist = FileExtensionWhitelist.objects.all()
        cache.set(cache_key, whitelist, settings.CACHE_TIMEOUT_2_HOURS)

    valid = file_extension_valid(str(file), whitelist, model_name)

    if not valid:
        raise serializers.ValidationError("File type/extension not supported")