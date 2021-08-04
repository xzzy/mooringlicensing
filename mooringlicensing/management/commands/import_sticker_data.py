import imaplib
import email
import ssl
import os
from confy import env
from django.core.management.base import BaseCommand
import base64
from email.header import decode_header, make_header

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
            raw_email = data[0][1]

            # converts byte literal to string removing b''
            raw_email_string = raw_email.decode('utf-8')
            email_message = email.message_from_string(raw_email_string)

            subject = str(make_header(decode_header(email_message["Subject"])))
            print('Title: ' + subject)
            print('From: ' + email_message['From'])
            # print('Body: ' + email_message.get_payload(decode=True))
            body = get_text(email_message)
            body = body.decode()
            print('Body: ' + body)

            # downloading attachments
            for part in email_message.walk():
                # this part comes from the snipped I don't understand yet...
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                fileName = part.get_filename()
                if bool(fileName):
                    filePath = os.path.join('./tmp/', fileName)
                    if not os.path.isfile(filePath):
                        fp = open(filePath, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()
                    subject = str(email_message).split("Subject: ", 1)[1].split("\nTo:", 1)[0]

            # mail = email.message_from_string(data[0][1].decode('utf-8'))
            #
            # subject = str(make_header(decode_header(mail["Subject"])))
            # print('Title: {}'.format(subject))
            #
            # for part in mail.walk():
            #     if part.get_content_maintype() == 'multipart':
            #         continue
            #     filename = part.get_filename()
            #     if not filename:
            #         body = base64.urlsafe_b64decode(part.get_payload().encode('ASCII')).decode('utf-8')
            #         print('body: {}'.format(body))
            #     else:
            #         with open('./' + filename, 'wb') as f:
            #             f.write(part.get_payload(decode=True))
            #             print('{} has been saved'.format(filename))

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


def get_text(msg):
    if msg.is_multipart():
        return get_text(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)