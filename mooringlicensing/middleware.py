# from django.core.urlresolvers import reverse
from django.urls import reverse
from django.shortcuts import redirect
from urllib.parse import quote_plus

import re
import datetime

from django.http import HttpResponseRedirect
from django.utils import timezone
#from mooringlicensing.components.bookings.models import ApplicationFee
from reversion.middleware  import RevisionMiddleware
from reversion.views import _request_creates_revision

import logging

logger = logging.getLogger(__name__)

CHECKOUT_PATH = re.compile('^/ledger/checkout/checkout')

# TODO: rework for system user (use system user values to determine redirect, redirect to sys user page)
class FirstTimeNagScreenMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.method == 'GET' and 'api' not in request.path and 'admin' not in request.path and 'static' not in request.path:
            # if not request.user.first_name or not request.user.last_name:
            if not request.user.first_name or not request.user.last_name or not request.user.residential_address_id or not request.user.postal_address_id:
                path_first_time = reverse('system-accounts-firstime')
                path_logout = reverse('logout')
                if request.path not in (path_first_time, path_logout):
                    logger.info('redirect')
                    return redirect(path_first_time + "?next=" + quote_plus(request.get_full_path()))
                else:
                    # We don't want to redirect the suer when the user is accessing the firsttime page or logout page.
                    pass
        response = self.get_response(request)
        return response


class CacheControlMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    # def process_response(self, request, response):
    def __call__(self, request):
        response = self.get_response(request)
        if request.path[:5] == '/api/' or request.path == '/':
            response['Cache-Control'] = 'private, no-store'
        elif request.path[:8] == '/static/':
            response['Cache-Control'] = 'public, max-age=300'
        return response


class RevisionOverrideMiddleware(RevisionMiddleware):

    """
        Wraps the entire request in a revision.

        override venv/lib/python2.7/site-packages/reversion/middleware.py
    """

	# exclude ledger payments/checkout from revision - hack to overcome basket (lagging status) issue/conflict with reversion
    def request_creates_revision(self, request):
        return _request_creates_revision(request) and 'checkout' not in request.get_full_path()
