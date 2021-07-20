import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from mooringlicensing.components.payments_ml.models import FeeConstructor

logger = logging.getLogger('log')


class FeeConstructorListener(object):

    @staticmethod
    @receiver(post_save, sender=FeeConstructor)
    def _post_save(sender, instance, **kwargs):
        instance.reconstruct_fees()
