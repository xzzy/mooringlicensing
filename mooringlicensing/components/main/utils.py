import datetime
from io import BytesIO
from pathlib import Path
from django.db.models import Q
from django.core.files.base import File, ContentFile
from ledger.settings_base import TIME_ZONE
from django.utils import timezone

import requests
import json
import pytz
from django.conf import settings
from django.core.cache import cache
from django.db import connection, transaction

from mooringlicensing.components.approvals.models import Sticker, WaitingListAllocation
from mooringlicensing.components.proposals.email import send_sticker_printing_batch_email
from mooringlicensing.components.proposals.models import (
        MooringBay, 
        Mooring, 
        Proposal, 
        StickerPrintingBatch, 
        MooringLicenceApplication
        )
from rest_framework import serializers
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from copy import deepcopy
import os
import logging
logger = logging.getLogger(__name__)

def add_cache_control(response):
    response['Cache-Control'] = 'private, no-store'
    return response

def retrieve_department_users():
    try:
        #res = requests.get('{}/api/v3/departmentuser?minimal'.format(settings.CMS_URL), auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
        res = requests.get('{}/api/v3/departmentuser/'.format(settings.CMS_URL), auth=(settings.LEDGER_USER, settings.LEDGER_PASS))
        res.raise_for_status()
        #import ipdb; ipdb.set_trace()
        #cache.set('department_users',json.loads(res.content).get('objects'),10800)
        cache.set('department_users',json.loads(res.content), 10800)
    except:
        raise

def get_department_user(email):
    try:
        res = requests.get('{}/api/users?email={}'.format(settings.CMS_URL,email), auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
        res.raise_for_status()
        data = json.loads(res.content).get('objects')
        if len(data) > 0:
            return data[0]
        else:
            return None
    except:
        raise

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

def reset_waiting_list_allocations(wla_list):
    try:
        records_updated = []
        with transaction.atomic():
            # send email
            #send_create_mooring_licence_application_email_notification(request, waiting_list_allocation)
            # update waiting_list_allocation
            for waiting_list_allocation in wla_list:
                waiting_list_allocation.status = 'current'
                #current_datetime = datetime.datetime.now(pytz.timezone(TIME_ZONE))
                now = timezone.localtime(timezone.now())
                waiting_list_allocation.wla_queue_date = now
                waiting_list_allocation.save()
                # discard MLA
                mla_qs = MooringLicenceApplication.objects.filter(
                        waiting_list_allocation=waiting_list_allocation,
                        processing_status='draft').order_by('-lodgement_date')
                mla = mla_qs[0] if mla_qs else None
                if mla:
                    mla.processing_status = 'discarded'
                    mla.customer_status = 'discarded'
                    mla.save()
                    records_updated.append(str(mla))
            # set wla order per bay
            for bay in MooringBay.objects.all():
                place = 1
                for w in WaitingListAllocation.objects.filter(
                        wla_queue_date__isnull=False, 
                        current_proposal__preferred_bay=bay,
                        status='current').order_by(
                                '-wla_queue_date'):
                    w.wla_order = place
                    w.save()
                    records_updated.append(str(w))
                    place += 1
            return [], records_updated
    except Exception as e:
        #raise e
        logger.error('retrieve_mooring_areas() error', exc_info=True)
        # email only prints len() of error list
        return ['check log',], records_updated

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

## Mooring Bookings API interactions
def retrieve_mooring_areas():
    records_updated = []
    try:
        url = settings.MOORING_BOOKINGS_API_URL + "all-mooring/" + settings.MOORING_BOOKINGS_API_KEY
        res = requests.get(url)
        res.raise_for_status()
        data = res.json().get('data')
        #return data
        # update Mooring records
        with transaction.atomic():
            for mooring in data:
                mooring_qs = Mooring.objects.filter(mooring_bookings_id=mooring.get("id"))
                if mooring_qs.count() > 0:
                    mo = mooring_qs[0]
                    orig_mo = deepcopy(mo)
                    #if mo.name != mooring.get("name"):
                    #    # only updates name field?
                    #    mo.name=mooring.get("name")
                    #    mo.save()
                    #    records_updated.append(str(mo.name))
                    mo.mooring_bookings_id=mooring.get("id")
                    mo.name=mooring.get("name")
                    mo.mooring_bay = MooringBay.objects.get(
                        mooring_bookings_id=mooring.get('marine_park_id'), 
                            active=True
                            )
                    mo.vessel_size_limit = mooring.get('vessel_size_limit')
                    mo.vessel_draft_limit = mooring.get('vessel_draft_limit')
                    mo.vessel_beam_limit = mooring.get('vessel_beam_limit')
                    mo.vessel_weight_limit = mooring.get('vessel_weight_limit')
                    mo.mooring_bookings_mooring_specification = mooring.get('mooring_specification')
                    mo.mooring_bookings_bay_id = mooring.get('marine_park_id')
                    mo.save()
                    if orig_mo != mo:
                        records_updated.append(str(mo.name))
                else:
                    mooring = Mooring.objects.create(
                            mooring_bookings_id=mooring.get("id"), 
                            name=mooring.get("name"),
                            mooring_bay = MooringBay.objects.get(
                                mooring_bookings_id=mooring.get('marine_park_id'), 
                                    active=True
                                    ),
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
            return [], records_updated

    except Exception as e:
        #raise e
        logger.error('retrieve_mooring_areas() error', exc_info=True)
        # email only prints len() of error list
        return ['check log',], records_updated

def retrieve_marine_parks():
    records_updated = []
    try:
        #import ipdb; ipdb.set_trace()
        # CRON (every night?)  Plus management button for manual control.
        url = settings.MOORING_BOOKINGS_API_URL + "marine-parks/" + settings.MOORING_BOOKINGS_API_KEY
        res = requests.get(url)
        res.raise_for_status()
        data = res.json().get('data')
        # update MooringBay records
        with transaction.atomic():
            for bay in data:
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
                #else:
                #    mooring_bay.active = True
                #    mooring_bay.save()
    except Exception as e:
        logger.error('retrieve_marine_parks() error', exc_info=True)
        return ['check log',], records_updated

def handle_validation_error(e):
    # if hasattr(e, 'error_dict'):
    #     raise serializers.ValidationError(repr(e.error_dict))
    # else:
    #     raise serializers.ValidationError(repr(e[0].encode('utf-8')))
    if hasattr(e, 'error_dict'):
        raise serializers.ValidationError(repr(e.error_dict))
    else:
        if hasattr(e, 'message'):
            raise serializers.ValidationError(e.message)
        else:
            raise


#def add_business_days(from_date, number_of_days):
#    """ given from_date and number_of_days, returns the next weekday date i.e. excludes Sat/Sun """
#    to_date = from_date
#    while number_of_days:
#        to_date += timedelta(1)
#        if to_date.weekday() < 5: # i.e. is not saturday or sunday
#            number_of_days -= 1
#    return to_date
#
#def get_next_weekday(from_date):
#    """ given from_date and number_of_days, returns the next weekday date i.e. excludes Sat/Sun """
#    if from_date.weekday() == 5: # i.e. Sat
#        from_date += timedelta(2)
#    elif from_date.weekday() == 6: # i.e. Sun
#        from_date += timedelta(1)
#
#    return from_date


def handle_validation_error(e):
    # if hasattr(e, 'error_dict'):
    #     raise serializers.ValidationError(repr(e.error_dict))
    # else:
    #     raise serializers.ValidationError(repr(e[0].encode('utf-8')))
    if hasattr(e, 'error_dict'):
        raise serializers.ValidationError(repr(e.error_dict))
    else:
        if hasattr(e, 'message'):
            raise serializers.ValidationError(e.message)
        else:
            raise


def sticker_export():
    # Note: if the user wants to apply for e.g. three new authorisations,
    # then the user needs to submit three applications. The system will
    # combine them onto one sticker if payment is received on one day
    # (applicant is notified to pay once RIA staff approve the application)
    stickers = Sticker.objects.filter(sticker_printing_batch__isnull=True)  # When sticker_printing_batch==null, status should always be 'printing'

    if stickers.count():
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
            'Sticker Number',
            'Vessel Registration Number',
            'Moorings',
            'Colour',
        ])
        for sticker in stickers:
            # column: Moorings
            bay_moorings = []
            for mooring in sticker.approval.moorings.all():
                bay_moorings.append(mooring.mooring_bay.name + ' ' + mooring.name)
            bay_moorings = ', '.join(bay_moorings)

            ws1.append([
                'date',
                sticker.first_name,
                sticker.last_name,
                sticker.postal_address_line1,
                sticker.postal_address_line2,
                'suburb',
                sticker.postal_address_state,
                sticker.postal_address_postcode,
                sticker.number,
                'v rego',
                bay_moorings,
                sticker.get_sticker_colour(),
            ])

        wb.save(virtual_workbook)

        batch_obj = StickerPrintingBatch.objects.create()
        filename = 'RIA-{}.xlsx'.format(batch_obj.uploaded_date.astimezone(pytz.timezone(TIME_ZONE)).strftime('%Y%m%d'))
        batch_obj._file.save(filename, virtual_workbook)
        batch_obj.name = filename
        batch_obj.save()

        # Update sticker objects
        stickers.update(
            sticker_printing_batch=batch_obj,  # Keep status 'printing' because we still have to wait for the sticker printed.
        )


def email_stickers_document():
    batches = StickerPrintingBatch.objects.filter(emailed_datetime__isnull=True)
    if batches.count():
        send_sticker_printing_batch_email(batches)
        batches.update(emailed_datetime=datetime.datetime.now(pytz.timezone(TIME_ZONE)))

