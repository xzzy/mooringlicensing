import logging

from django.contrib.auth.models import Group

from mooringlicensing import settings
from mooringlicensing.components.approvals.models import AgeGroup, AdmissionType
from mooringlicensing.components.main.models import ApplicationType, GlobalSettings
from mooringlicensing.components.proposals.models import ProposalType, Proposal, ProposalAssessorGroup, \
    ProposalApproverGroup

logger = logging.getLogger(__name__)


class DefaultDataManager(object):

    def __init__(self):
        # Proposal Types
        for item in settings.PROPOSAL_TYPES:
            try:
                type, created = ProposalType.objects.get_or_create(code=item[0])
                if created:
                    type.description = item[1]
                    type.save()
                    logger.info("Created ProposalType: {}".format(item[1]))
            except Exception as e:
                logger.error('{}, ProposalType: {}'.format(e, item[1]))

        # Application Types
        for item in Proposal.__subclasses__():
            # Create record(s) based on the existence of the subclasses
            if hasattr(item, 'code'):
                try:
                    type, created = ApplicationType.objects.get_or_create(code=item.code)
                    if created:
                        type.description = item.description
                        type.oracle_code = item.oracle_code
                        type.save()
                        logger.info("Created ApplicationType: {}".format(item.description))
                except Exception as e:
                    logger.error('{}, ApplicationType: {}'.format(e, item.code))
        try:
            # Create record for the DCV Permit
            type, created = ApplicationType.objects.get_or_create(code=settings.APPLICATION_TYPE_DCV_PERMIT['code'])
            if created:
                type.description = settings.APPLICATION_TYPE_DCV_PERMIT['description']
                type.oracle_code = settings.APPLICATION_TYPE_DCV_PERMIT['oracle_code']
                type.save()
                logger.info("Created ApplicationType: {}".format(type.description))

            # Create record for the DCV Admission
            type, created = ApplicationType.objects.get_or_create(code=settings.APPLICATION_TYPE_DCV_ADMISSION['code'])
            if created:
                type.description = settings.APPLICATION_TYPE_DCV_ADMISSION['description']
                type.oracle_code = settings.APPLICATION_TYPE_DCV_ADMISSION['oracle_code']
                type.save()
                logger.info("Created ApplicationType: {}".format(type.description))
        except Exception as e:
            logger.error('{}, ApplicationType: {}'.format(e, item.code))

        # Assessor Group
        for item in settings.ASSESSOR_GROUPS:
            try:
                group, created = ProposalAssessorGroup.objects.get_or_create(name=item)
                if created:
                    logger.info("Created ProposalAssessorGroup: {}".format(item))
            except Exception as e:
                logger.error('{}, ProposalAssessorGroup: {}'.format(e, item))

        # Approver Group
        for item in settings.APPROVER_GROUPS:
            try:
                group, created = ProposalApproverGroup.objects.get_or_create(name=item)
                if created:
                    logger.info("Created ProposalApproverGroup: {}".format(item))
            except Exception as e:
                logger.error('{}, ProposalApproverGroup: {}'.format(e, item))

        # Store
        for item in GlobalSettings.default_values:
            try:
                obj, created = GlobalSettings.objects.get_or_create(key=item[0])
                if created:
                    obj.value = item[1]
                    obj.save()
                    logger.info("Created {}: {}".format(item[0], item[1]))
            except Exception as e:
                logger.error('{}, Key: {}'.format(e, item[0]))

        # AgeGroup for the DcvAdmission fees
        for item in AgeGroup.NAME_CHOICES:
            try:
                type, created = AgeGroup.objects.get_or_create(code=item[0])
                if created:
                    logger.info("Created AgeGroup: {}".format(item[1]))
            except Exception as e:
                logger.error('{}, AgeGroup: {}'.format(e, item[1]))

        # AdmissionType for the DcvAdmission fees
        for item in AdmissionType.TYPE_CHOICES:
            try:
                type, created = AdmissionType.objects.get_or_create(code=item[0])
                if created:
                    logger.info("Created AdmissionType: {}".format(item[1]))
            except Exception as e:
                logger.error('{}, AdmissionType: {}'.format(e, item[1]))

        # Groups
        for group_name in settings.CUSTOM_GROUPS:
            try:
                group, created = Group.objects.get_or_create(name=group_name)
                if created:
                    logger.info("Created group: {}".format(group_name))
            except Exception as e:
                logger.error('{}, Group name: {}'.format(e, group_name))
