from rest_framework.exceptions import APIException,PermissionDenied

class ProposalNotAuthorized(PermissionDenied):
    default_detail = 'You are not authorised to work on this proposal'
    default_code = 'proposal_not_authorized'

class ProposalNotComplete(APIException): #TODO currently unused, should be
    status_code = 400
    default_detail = 'The proposal is not complete'
    default_code = 'proposal_incoplete'

class ProposalMissingFields(APIException): #TODO currently unused, should be
    status_code = 400
    default_detail = 'The proposal has missing required fields'
    default_code = 'proposal_missing_fields'
