import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from mooringlicensing.components.proposals.models import Proposal, CompanyOwnership, VesselOwnershipCompanyOwnership

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

        # Update the status of the vessel_ownersip_company_ownership
        if instance.vessel_ownership:
            # company_ownerships = instance.vessel_ownership.company_ownerships.filter(
            #     vessel=instance.vessel_ownership.vessel, 
            #     vesselownershipcompanyownership__status__in=[VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_DRAFT,]
            # )
            # for company_ownership in company_ownerships:
            #     # For each company_ownership with the 'draft' status
            #     vessel_ownership_company_ownerships = VesselOwnershipCompanyOwnership.objects.filter(
            #         company_ownership=company_ownership, 
            #         vessel_ownership=instance.vessel_ownership, 
            #         status=VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_DRAFT
            #     )
            #     for vessel_ownership_company_ownership in vessel_ownership_company_ownerships:
            #         if instance.processing_status in [Proposal.PROCESSING_STATUS_APPROVED, Proposal.PROCESSING_STATUS_PRINTING_STICKER,]:
            #             new_status = VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED
            #         elif instance.processing_status in [Proposal.PROCESSING_STATUS_DECLINED,]:
            #             new_status = VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_DECLINED
            #         vessel_ownership_company_ownership.status = new_status
            #         vessel_ownership_company_ownership.save()
            #         logger.info(f'Status: [{new_status}] has been set to the VesselOwnershipCompanyOwnership: [{vessel_ownership_company_ownership}].')

            vocos_draft = VesselOwnershipCompanyOwnership.objects.filter(
                vessel_ownership=instance.vessel_ownership, 
                status=VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_DRAFT
            )
            for voco_draft in vocos_draft:
                new_status = ''
                if instance.processing_status in [Proposal.PROCESSING_STATUS_APPROVED, Proposal.PROCESSING_STATUS_PRINTING_STICKER,]:
                    voco_draft.status = VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED
                    voco_draft.save()
                    logger.info(f'Status: [{new_status}] has been set to the VesselOwnershipCompanyOwnership: [{voco_draft}].')

                    # Set status 'old' to the previous 'approved' voco
                    vocos_approved = VesselOwnershipCompanyOwnership.objects.filter(
                        vessel_ownership=instance.vessel_ownership, 
                        status=VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED
                    ).exclude(id=voco_draft.id)
                    for voco_approved in vocos_approved:
                        voco_approved.status = VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_OLD
                        voco_approved.save()
                        logger.info(f'Status: [{VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_OLD}] has been set to the VesselOwnershipCompanyOwnership: [{voco_approved}].')
                elif instance.processing_status in [Proposal.PROCESSING_STATUS_DECLINED,]:
                    voco_draft.status = VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_DECLINED
                    voco_draft.save()
                    logger.info(f'Status: [{new_status}] has been set to the VesselOwnershipCompanyOwnership: [{voco_draft}].')

            # for voco_approved in vocos_approved:
            #     if voco_approved.id not in vocos_approved_ids:  # Avoid the vocos approved just now
            #         voco_approved.status = VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_OLD
            #         voco_approved.save()
            #         logger.info(f'Status: [{VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_OLD}] has been set to the VesselOwnershipCompanyOwnership: [{voco_approved}].')

            


