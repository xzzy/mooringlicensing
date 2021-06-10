from django.core.management.base import BaseCommand

from mooringlicensing.components.main.utils import sticker_export, email_stickers_document


class Command(BaseCommand):
    help = 'Export and email sticker data'

    def handle(self, *args, **options):
        sticker_export()
        email_stickers_document()
