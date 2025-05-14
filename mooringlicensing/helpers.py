from __future__ import unicode_literals
from django.conf import settings
from django.core.cache import cache

import logging
import ledger_api_client

from rest_framework import serializers

from mooringlicensing.components.proposals.models import Proposal

logger = logging.getLogger(__name__)

def belongs_to(user, group_name):
    """
    Check if the user belongs to the given group.
    :param user:
    :param group_name:
    :return:
    """
    if user.is_superuser:
        return True
    
    belongs_to_value = cache.get(
        "User-belongs_to" + str(user.id) + "group_name:" + group_name
    )
    if belongs_to_value is None:
        belongs_to_value = False
        system_group = ledger_api_client.managed_models.SystemGroup.objects.filter(name=group_name)
        if system_group.exists():
            if user.id in system_group.first().get_system_group_member_ids():
                belongs_to_value = True
            cache.set(
                "User-belongs_to" + str(user.id) + "group_name:" + group_name,
                belongs_to_value,
                3600,
            )
    return belongs_to_value

def is_model_backend(request):
    # Return True if user logged in via single sign-on (i.e. an internal)
    return 'ModelBackend' in request.session.get('_auth_user_backend')

def is_email_auth_backend(request):
    # Return True if user logged in via social_auth (i.e. an external user signing in with a login-token)
    return 'EmailAuth' in request.session.get('_auth_user_backend')

def is_mooringlicensing_admin(request):
    return request.user.is_authenticated and (belongs_to(request.user, settings.GROUP_MOORING_LICENSING_ADMIN))

def is_account_management_user(request):
    return request.user.is_authenticated and (belongs_to(request.user, settings.GROUP_ACCOUNT_MANAGEMENT_USER))

def is_customer(request):
    return request.user.is_authenticated and (is_model_backend(request) or is_email_auth_backend(request))

def is_internal(request):
    if request.user.is_authenticated:
        for i in settings.INTERNAL_GROUPS:
            if belongs_to(request.user, i):
                return True
    return False

def is_internal_user(user):
    if user.is_authenticated:
        for i in settings.INTERNAL_GROUPS:
            if belongs_to(user, i):
                return True
    return False

def is_authorised_to_pay_auto_approved(request, instance):
    if (instance.auto_approve and 
        (request.user.email == instance.applicant_email or is_internal(request))
        ):
        return True
    return False

def is_authorised_to_modify(request, instance):
    authorised = True

    authorised &= instance.processing_status in [Proposal.PROCESSING_STATUS_DRAFT]
    authorised &= (request.user.email == instance.applicant_email or is_internal(request))

    if not authorised:
        logger.warning(f'User: [{request.user}] is not authorised to modify this proposal: [{instance}].  Raise an error.')
        raise serializers.ValidationError('You are not authorised to modify this application.')
    
def is_authorised_to_submit_documents(request, instance):
    authorised = True

    authorised &= instance.processing_status in [Proposal.PROCESSING_STATUS_AWAITING_DOCUMENTS]
    authorised &= (request.user.email == instance.applicant_email or is_internal(request))

    if not authorised:
        logger.warning(f'User: [{request.user}] is not authorised to modify this proposal: [{instance}].  Raise an error.')
        raise serializers.ValidationError('You are not authorised to modify this application.')

def is_applicant_address_set(instance):

    applicant = instance.proposal_applicant

    #residential address
    if (
        not applicant.residential_address_line1 or 
        not applicant.residential_address_locality or 
        not applicant.residential_address_state or 
        not applicant.residential_address_country or 
        not applicant.residential_address_postcode
        ):
        raise serializers.ValidationError('Residential Address details not provided')

    #postal same as residential OR postal address
    if (
        not applicant.postal_address_line1 or 
        not applicant.postal_address_locality or 
        not applicant.postal_address_state or 
        not applicant.postal_address_country or 
        not applicant.postal_address_postcode       
        ):
        raise serializers.ValidationError('Postal Address details not provided')