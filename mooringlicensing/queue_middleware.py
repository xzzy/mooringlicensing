import requests
from django.conf import settings
from django.http import HttpResponse
from mooringlicensing.helpers import is_internal

class QueueControl(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_key = ''
        if settings.WAITING_QUEUE_ENABLED is True:
            # Required for ledger to send completion signal after payment is received.
            # NOTE: add dcv admission/permit payment views when implemented
            if (request.path.startswith('/ledger-api-success-callback/') 
                or request.path.startswith('/success/fee/') 
                or request.path.startswith('/sticker_replacement_fee_success/') 
                or request.path.startswith('/sticker_replacement_fee_success_preload/')):
                response= self.get_response(request)
                return response
            
            sitequeuesession = request.COOKIES.get('sitequeuesession', None)
            if (request.path.startswith('/') and not is_internal(request)):
                try:
                    if 'HTTP_HOST' in request.META:
                        if settings.QUEUE_ACTIVE_HOSTS == request.META.get('HTTP_HOST',''):
                            if settings.QUEUE_WAITING_URL:
                                if sitequeuesession is None:
                                    sitequeuesession=''
                                         
                                    url = settings.QUEUE_BACKEND_URL+"/api/check-create-session/?session_key="+sitequeuesession+"&queue_group="+settings.QUEUE_GROUP_NAME
                                    resp = requests.get(url, data = {}, cookies={},  verify=False, timeout=10)
                                                                 
                                    queue_json = resp.json()
                                    if 'session_key' in queue_json:
                                        session_key = queue_json['session_key']
                                   
                                    if queue_json['status'] == 'Waiting': 
                                        response =HttpResponse("<script>window.location.replace('"+queue_json['queue_waiting_room_url']+"');</script>Redirecting")
                                        print('You are waiting : '+str(sitequeuesession))
                                        return response
                                else:
                                    print('Active Session')
                                               
                except Exception as e:
                    print(e)
                    print("ERROR LOADING QUEUE")

        response = self.get_response(request)
        if len(session_key) > 5:
            response.set_cookie('sitequeuesession', session_key, domain=settings.QUEUE_DOMAIN)
        return response