from rest_framework.permissions import BasePermission

from mooringlicensing.helpers import (
    is_internal,
)

class InternalProposalPermission(BasePermission):
    """
    Proposal permission for internal users, essentially any member of 
    any of the existing internal system groups as listed in settings.INTERNAL_GROUPS

    This permission allows the internal reading of proposals (using internal detailed serializers)
    and creation of proposals on an external user's behalf

    Intended to be non-specific with regards to the given proposal type
    """

    def has_permission(self, request, view):
        return is_internal(request)