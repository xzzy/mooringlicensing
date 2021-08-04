import imaplib
import email
import ssl
from confy import env
from django.core.management.base import BaseCommand

from mooringlicensing.components.main.utils import sticker_export, email_stickers_document

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import emails and process sticker data'

    def handle(self, *args, **options):
        errors = []
        updates = []

        sticker_email_host = env('STICKER_EMAIL_HOST', '')
        sticker_email_port = env('STICKER_EMAIL_PORT', '')
        sticker_email_username = env('STICKER_EMAIL_USERNAME', '')
        sticker_email_password = env('STICKER_EMAIL_PASSWORD', '')

        if not sticker_email_host or not sticker_email_port or not sticker_email_username or not sticker_email_password:
            raise Exception('Configure email settings to process stickers')

        context = ssl.create_default_context()
        imapclient = imaplib.IMAP4_SSL(sticker_email_host, sticker_email_port, ssl_context=context)

        # login
        imapclient.login(sticker_email_username, sticker_email_password)

        """
        Retrieve messages
        """
        imapclient.select()  # Select mail box
        typ, data = imapclient.search(None, "ALL")  # data = [b"1 2 3 4 ..."]
        datas = data[0].split()
        fetch_num = 5  # The number of messages to fetch
        if (len(datas) - fetch_num) < 0:
            fetch_num = len(datas)
        msg_list = []
        for num in datas[len(datas) - fetch_num::]:
            typ, data = imapclient.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            msg_list.append(msg)
        imapclient.close()
        imapclient.logout()

        for msg in msg_list:
            print(msg)

        # updates, errors = sticker_export()
        # success_filenames, error_filenames = email_stickers_document()

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        # error_count = len(errors) + len(error_filenames)
        error_count = len(errors)
        err_str = '<strong style="color: red;">Errors: {}</strong>'.format(error_count) if error_count else '<strong style="color: green;">Errors: 0</strong>'
        msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        logger.info(msg)
        print(msg)  # will redirect to cron_tasks.log file, by the parent script
