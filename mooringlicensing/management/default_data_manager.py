import logging
from mooringlicensing import settings
from mooringlicensing.components.approvals.models import Approval
from mooringlicensing.components.main.models import ApplicationType
from mooringlicensing.components.proposals.models import ProposalType


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
        for item in Approval.__subclasses__():
            # Create record(s) based on the existence of the subclasses
            if hasattr(item, 'code'):
                try:
                    type, created = ApplicationType.objects.get_or_create(code=item.code)
                    if created:
                        type.description = item.description
                        type.save()
                        logger.info("Created ApplicationType: {}".format(item.description))
                except Exception as e:
                    logger.error('{}, ApplicationType: {}'.format(e, item.code))
