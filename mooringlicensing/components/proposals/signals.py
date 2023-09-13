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
            # latest_company_ownership = instance.vessel_ownership.get_latest_company_ownership([CompanyOwnership.COMPANY_OWNERSHIP_STATUS_DRAFT,])
            company_ownerships = instance.vessel_ownership.company_ownerships.filter(
                vessel=instance.vessel_ownership.vessel, 
                status__in=[CompanyOwnership.COMPANY_OWNERSHIP_STATUS_DRAFT,]
            )
            for company_ownership in company_ownerships:
                # There is a 'draft' company_ownership
                if instance.processing_status in [Proposal.PROCESSING_STATUS_APPROVED, Proposal.PROCESSING_STATUS_PRINTING_STICKER,]:
                    company_ownership.status = CompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED
                    company_ownership.save()
                    logger.info(f'Status: [{CompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED}] has been set to the CompanyOwnership: [{company_ownership}].')
                elif instance.processing_status in [Proposal.PROCESSING_STATUS_DECLINED,]:
                    company_ownership.status = CompanyOwnership.COMPANY_OWNERSHIP_STATUS_DECLINED
                    company_ownership.save()
                    logger.info(f'Status: [{CompanyOwnership.COMPANY_OWNERSHIP_STATUS_DECLINED}] has been set to the CompanyOwnership: [{company_ownership}].')

            if instance.individual_owner:
                # The proposal saved just now is for individual owner
                company_ownerships = instance.vessel_ownership.company_ownerships.filter(
                    vessel=instance.vessel_ownership.vessel, 
                    status__in=[CompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED,],
                )
                for company_ownership in company_ownerships:
                    company_ownership.status = CompanyOwnership.COMPANY_OWNERSHIP_STATUS_OLD
                    company_ownership.save()
                    logger.info(f'Status: [{CompanyOwnership.COMPANY_OWNERSHIP_STATUS_OLD}] has been set to the CompanyOwnership: [{company_ownership}].')



