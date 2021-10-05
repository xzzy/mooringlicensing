from django.conf import settings
from ledger.accounts.models import EmailUser


def get_user_as_email_user(sender):
    try:
        sender_user = EmailUser.objects.get(email__icontains=sender)
    except:
        EmailUser.objects.create(email=sender, password='')
        sender_user = EmailUser.objects.get(email__icontains=sender)
    return sender_user


def make_url_for_internal(url):
    if '-internal' not in url:
        if '-dev' in url:
            url = url.replace('-dev', '-dev-internal')
        elif '-uat' in url:
            url = url.replace('-uat', '-uat-internal')
    return url


def get_public_url(request=None):
    if request:
        # web_url = request.META.get('HTTP_HOST', None)
        web_url = '{}://{}'.format(request.scheme, request.get_host())
    else:
        web_url = settings.SITE_URL if settings.SITE_URL else ''
    return web_url