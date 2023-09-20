import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from mooringlicensing.components.proposals.models import AuthorisedUserApplication, MooringLicenceApplication, Proposal, CompanyOwnership, VesselOwnershipCompanyOwnership

logger = logging.getLogger(__name__)


# class TestListener(object):
#     @staticmethod
#     @receiver(post_save, sender=MooringLicenceApplication)
#     def _post_save(sender, instance, **kwargs):
#         logger.info(f'sender: [{sender}]')
#         logger.info(f'instance: [{instance}]')

class ProposalListener(object):
    @staticmethod
    @receiver(post_save, sender=Proposal)
    @receiver(post_save, sender=MooringLicenceApplication)  # To make sure this signal is called, register 'MooringLicenceApplication' too as well as 'Proposal'.
                                                            # Without this line, in some case this _post_save() signal is not called even after saving the MLApplication.
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
            vocos_draft = VesselOwnershipCompanyOwnership.objects.filter(
                vessel_ownership=instance.vessel_ownership, 
                status=VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_DRAFT
            )
            for voco_draft in vocos_draft:
                if instance.processing_status in [Proposal.PROCESSING_STATUS_APPROVED, Proposal.PROCESSING_STATUS_PRINTING_STICKER,]:
                    voco_draft.status = VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED
                    voco_draft.save()
                    logger.info(f'Status: [{VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED}] has been set to the VesselOwnershipCompanyOwnership: [{voco_draft}].')

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
                    logger.info(f'Status: [{VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_DECLINED}] has been set to the VesselOwnershipCompanyOwnership: [{voco_draft}].')

            if instance.processing_status in [Proposal.PROCESSING_STATUS_APPROVED, Proposal.PROCESSING_STATUS_PRINTING_STICKER,]:
                # if instance.vessel_ownership.individual_owner:
                if instance.individual_owner:
                    # Proposal.status is 'approved'/'printing_sticker' and the vessel is individually owned.

                    # Change company_ownership with the 'approved' status to 'old' status
                    vocos_approved = VesselOwnershipCompanyOwnership.objects.filter(
                        vessel_ownership=instance.vessel_ownership, 
                        status=VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_APPROVED
                    )
                    for voco_approved in vocos_approved:
                        voco_approved.status = VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_OLD
                        voco_approved.save()
                        logger.info(f'Status: [{VesselOwnershipCompanyOwnership.COMPANY_OWNERSHIP_STATUS_OLD}] has been set to the VesselOwnershipCompanyOwnership: [{voco_approved}].')
