from rest_framework.permissions import BasePermission

from mooringlicensing.helpers import (
    is_internal,
    belongs_to,
)

from django.conf import settings
from rest_framework import permissions

class InternalCompliancePermission(BasePermission):
    """
    Compliance permission for internal users, essentially any member of 
    any of the existing internal system groups as listed in settings.INTERNAL_GROUPS

    Intended to be non-specific with regards to the given compliance type
    """
    def has_permission(self, request, view):
        return is_internal(request)
    
class ComplianceAssessorPermission(InternalCompliancePermission):
    """
    Permission check that accounts for user group membership and the application type of the compliance
    """
    ASSESSOR_AUTH_GROUPS = {
        "wla":[settings.GROUP_ASSESSOR_WAITING_LIST, settings.GROUP_MOORING_LICENSING_ADMIN],
        "aaa":[settings.GROUP_ASSESSOR_ANNUAL_ADMISSION, settings.GROUP_MOORING_LICENSING_ADMIN],
        "aua":[settings.GROUP_ASSESSOR_AUTHORISED_USER, settings.GROUP_MOORING_LICENSING_ADMIN],
        "mla":[settings.GROUP_ASSESSOR_MOORING_LICENCE, settings.GROUP_MOORING_LICENSING_ADMIN],
    }

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        #accounts for when non-safe methods need to be protected 
        #but still allows internal user access to the viewset
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if obj.proposal and obj.proposal.child_obj and obj.proposal.child_obj.code:
            for i in self.ASSESSOR_AUTH_GROUPS[obj.child_obj.code]:
                if belongs_to(request.user, i):
                    return True

        return False