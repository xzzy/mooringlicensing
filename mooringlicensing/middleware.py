from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.http import urlquote_plus

import re
import datetime

from django.http import HttpResponseRedirect
from django.utils import timezone
#from mooringlicensing.components.bookings.models import ApplicationFee
from reversion.middleware  import RevisionMiddleware
from reversion.views import _request_creates_revision

CHECKOUT_PATH = re.compile('^/ledger/checkout/checkout')

class FirstTimeNagScreenMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated() and request.method == 'GET' and 'api' not in request.path and 'admin' not in request.path and 'static' not in request.path:
            if (not request.user.first_name or not request.user.last_name):
                path_ft = reverse('first_time')
                path_logout = reverse('accounts:logout')
                if request.path not in (path_ft, path_logout):
                    return redirect(reverse('first_time')+"?next="+urlquote_plus(request.get_full_path()))

class CacheControlMiddleware(object):
    def process_response(self, request, response):
        if request.path[:5] == '/api/' or request.path == '/':
            response['Cache-Control'] = 'private, no-store'
        elif request.path[:8] == '/static/':
            response['Cache-Control'] = 'public, max-age=86400'
        return response

class RevisionOverrideMiddleware(RevisionMiddleware):

    """
        Wraps the entire request in a revision.

        override venv/lib/python2.7/site-packages/reversion/middleware.py
    """

	# exclude ledger payments/checkout from revision - hack to overcome basket (lagging status) issue/conflict with reversion
    def request_creates_revision(self, request):
        return _request_creates_revision(request) and 'checkout' not in request.get_full_path()
