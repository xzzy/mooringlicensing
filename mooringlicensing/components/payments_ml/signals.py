import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from mooringlicensing import settings
from mooringlicensing.components.approvals.models import AgeGroup, AdmissionType
from mooringlicensing.components.payments_ml.models import FeeConstructor, FeeItem
from mooringlicensing.components.proposals.models import ProposalType

logger = logging.getLogger('log')


class FeeConstructorListener(object):

    @staticmethod
    @receiver(post_save, sender=FeeConstructor)
    def _post_save(sender, instance, **kwargs):
        proposal_types = ProposalType.objects.all()
        valid_fee_item_ids = []  # We want to keep these fee items under this fee constructor object.

        try:
            for fee_period in instance.fee_season.fee_periods.all():
                for vessel_size_category in instance.vessel_size_category_group.vessel_size_categories.all():
                    if instance.application_type.code == settings.APPLICATION_TYPE_DCV_PERMIT['code']:
                        # For DcvPermit, no proposal type for-loop
                        fee_item, created = FeeItem.objects.get_or_create(fee_constructor=instance,
                                                                          fee_period=fee_period,
                                                                          vessel_size_category=vessel_size_category,
                                                                          proposal_type=None)
                        valid_fee_item_ids.append(fee_item.id)
                        if created:
                            logger.info(
                                'FeeItem created: {} - {}'.format(fee_period.name,
                                                                       vessel_size_category.name))

                    elif instance.application_type.code == settings.APPLICATION_TYPE_DCV_ADMISSION['code']:
                        # For DcvAdmission, no proposal type for-loop
                        for age_gruop in AgeGroup.objects.all():
                            for admission_type in AdmissionType.objects.all():
                                fee_item, created = FeeItem.objects.get_or_create(fee_constructor=instance,
                                                                                  fee_period=fee_period,
                                                                                  vessel_size_category=vessel_size_category,
                                                                                  age_group=age_gruop,
                                                                                  admission_type=admission_type,
                                                                                  proposal_type=None)
                                valid_fee_item_ids.append(fee_item.id)
                                if created:
                                    logger.info(
                                        'FeeItem created: {} - {} - {} - {}'.format(fee_period.name,
                                                                                         vessel_size_category.name,
                                                                                         age_gruop,
                                                                                         admission_type))
                    else:
                        for proposal_type in proposal_types:
                            fee_item, created = FeeItem.objects.get_or_create(fee_constructor=instance,
                                                                              fee_period=fee_period,
                                                                              vessel_size_category=vessel_size_category,
                                                                              proposal_type=proposal_type)
                            valid_fee_item_ids.append(fee_item.id)
                            if created:
                                logger.info('FeeItem created: {} - {} - {}'.format(fee_period.name,
                                                                                   vessel_size_category.name,
                                                                                   proposal_type.description))

            # Delete unused onl fee_items
            if instance.num_of_times_used_for_payment == 0:
                unneeded_fee_items = FeeItem.objects.filter(fee_constructor=instance).exclude(id__in=valid_fee_item_ids)
                if unneeded_fee_items:
                    unneeded_fee_item_ids = [item.id for item in unneeded_fee_items]
                    unneeded_fee_items.delete()
                    logger.info('FeeItem deleted: FeeItem ids: {}'.format(unneeded_fee_item_ids))
        except Exception as e:
            print(e)