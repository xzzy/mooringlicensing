import requests
import json
from datetime import timedelta, date, datetime
import pytz
from django.conf import settings
from django.core.cache import cache
from django.db import connection, transaction
from mooringlicensing.components.proposals.models import MooringBay


def retrieve_department_users():
    try:
        res = requests.get('{}/api/users?minimal'.format(settings.CMS_URL), auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
        res.raise_for_status()
        cache.set('department_users',json.loads(res.content).get('objects'),10800)
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

## Mooring Bookings API interactions
def retrieve_mooring_areas():
    url = settings.MOORING_BOOKINGS_API_URL + "all-mooring/" + settings.MOORING_BOOKINGS_API_KEY
    res = requests.get(url)
    res.raise_for_status()
    data = res.json().get('data')
    return data

def retrieve_marine_parks():
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
                else:
                    mooring_bay = MooringBay.objects.create(mooring_bookings_id=bay.get("id"), name=bay.get("name"))
                    print(mooring_bay)

        # update active status of any MooringBay records not found in api data
        for mooring_bay in MooringBay.objects.all():
            if mooring_bay not in [x.get("id") for x in data]:
                mooring_bay.active = False
                mooring_bay.save()


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


