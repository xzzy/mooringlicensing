import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from mooringlicensing.components.proposals.models import Proposal, CompanyOwnership

logger = logging.getLogger(__name__)

class ProposalListener(object):

    @staticmethod
    @receiver(post_save, sender=Proposal)
    def _post_save(sender, instance, **kwargs):
        if instance.processing_status in [
            Proposal.PROCESSING_STATUS_APPROVED,
            Proposal.PROCESSING_STATUS_DECLINED,
            Proposal.PROCESSING_STATUS_DISCARDED,
            Proposal.PROCESSING_STATUS_EXPIRED,
        ]:
            company_ownerships = CompanyOwnership.objects.filter(blocking_proposal=instance)
            for company_ownership in company_ownerships:
                company_ownership.blocking_proposal = None
                company_ownership.save()
                logger.info(f'BlockingProposal: [{instance.lodgement_number}] has been removed from the CompanyOwnership: [{company_ownership}]')

        # Update the status of the company_ownership
        if instance.vessel_ownership:
            latest_company_ownership = instance.vessel_ownership.get_latest_company_ownership([CompanyOwnership.COMPANY_OWNERSHIP_STATUS_DRAFT,])
            if latest_company_ownership:
                # There is a 'draft' company_ownership
                if instance.processing_status in [Proposal.PROCESSING_STATUS_APPROVED, Proposal.PROCESSING_STATUS_PRINTING_STICKER,]:
                    latest_company_ownership.status = CompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED
                    latest_company_ownership.save()
                    logger.info(f'Status: [{CompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED}] has been set to the CompanyOwnership: [{latest_company_ownership}].')
                elif instance.processing_status in [Proposal.PROCESSING_STATUS_DECLINED,]:
                    latest_company_ownership.status = CompanyOwnership.COMPANY_OWNERSHIP_STATUS_DECLINED
                    latest_company_ownership.save()
                    logger.info(f'Status: [{CompanyOwnership.COMPANY_OWNERSHIP_STATUS_DECLINED}] has been set to the CompanyOwnership: [{latest_company_ownership}].')
