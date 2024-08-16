from mooringlicensing.components.proposals.models import (
    WaitingListApplication,
    MooringLicenceApplication
)
from mooringlicensing.components.approvals.models import (
    WaitingListAllocation, 
    MooringLicence
)

def get_wla_allowed(user):
    wla_allowed = True
    # Person can have only one WLA, Waiting Liast application, Mooring Licence and Mooring Licence application
    rule1 = WaitingListApplication.get_intermediate_proposals(user.id)
    rule2 = WaitingListAllocation.get_intermediate_approvals(user.id)
    rule3 = MooringLicenceApplication.get_intermediate_proposals(user.id)
    rule4 = MooringLicence.get_valid_approvals(user.id)

    if rule1 or rule2 or rule3 or rule4:
        wla_allowed = False

    return wla_allowed