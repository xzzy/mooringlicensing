from django.conf import settings
# from ledger.accounts.models import EmailUser,Address, Profile,EmailIdentity, EmailUserAction, EmailUserLogEntry, CommunicationsLogEntry
from ledger_api_client.ledger_models import EmailUserRO, Address
from ledger_api_client.managed_models import SystemUser, SystemUserAddress
from mooringlicensing.components.main.serializers import CommunicationLogEntrySerializer
from mooringlicensing.components.organisations.models import (
                                    Organisation,
                                )
from mooringlicensing.components.proposals.models import Proposal, ProposalApplicant
from mooringlicensing.components.organisations.utils import can_admin_org, is_consultant
from rest_framework import serializers

from mooringlicensing.components.users.models import EmailUserLogEntry
# from ledger.accounts.utils import in_dbca_domain
from mooringlicensing.helpers import is_mooringlicensing_admin, in_dbca_domain
# from ledger.payments.helpers import is_payment_admin
from ledger_api_client.helpers import is_payment_admin

#TODO - status unclear but may need removal (determine how organisations work)
class UserOrganisationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='organisation.name')
    abn = serializers.CharField(source='organisation.abn')
    email = serializers.SerializerMethodField()
    is_consultant = serializers.SerializerMethodField(read_only=True)
    is_admin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Organisation
        fields = (
            'id',
            'name',
            'abn',
            'email',
            'is_consultant',
            'is_admin',
        )

    def get_is_admin(self, obj):
        user = EmailUserRO.objects.get(id=self.context.get('user_id'))
        return can_admin_org(obj, user)

    def get_is_consultant(self, obj):
        user = EmailUserRO.objects.get(id=self.context.get('user_id'))
        return is_consultant(obj, user)

    def get_email(self, obj):
        email = EmailUserRO.objects.get(id=self.context.get('user_id')).email
        return email

#TODO decom once system user in place
class ProposalApplicantForEndorserSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProposalApplicant
        fields = (
            'id',
            'last_name',
            'first_name',
            'email',
            'phone_number',
        )

#TODO decom once system user in place (?)
class EmailUserRoForEndorserSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmailUserRO
        fields = (
            'id',
            'last_name',
            'first_name',
            'email',
            'phone_number',
        )

#TODO decom once system user in place (?)
class EmailUserRoSerializer(serializers.ModelSerializer):
    residential_line1 = serializers.CharField(source='residential_address.line1')
    residential_line2 = serializers.CharField(source='residential_address.line2')
    residential_line3 = serializers.CharField(source='residential_address.line3')
    residential_locality = serializers.CharField(source='residential_address.locality')
    residential_state = serializers.CharField(source='residential_address.state')
    residential_country = serializers.CharField(source='residential_address.country')
    residential_postcode = serializers.CharField(source='residential_address.postcode')
    postal_line1 = serializers.CharField(source='postal_address.line1')
    postal_line2 = serializers.CharField(source='postal_address.line2')
    postal_line3 = serializers.CharField(source='postal_address.line3')
    postal_locality = serializers.CharField(source='postal_address.locality')
    postal_state = serializers.CharField(source='postal_address.state')
    postal_country = serializers.CharField(source='postal_address.country')
    postal_postcode = serializers.CharField(source='postal_address.postcode')

    class Meta:
        model = EmailUserRO
        fields = (
            'id',
            'last_name',
            'first_name',
            'dob',

            'residential_line1',
            'residential_line2',
            'residential_line3',
            'residential_locality',
            'residential_state',
            'residential_country',
            'residential_postcode',

            'postal_same_as_residential',

            'postal_line1',
            'postal_line2',
            'postal_line3',
            'postal_locality',
            'postal_state',
            'postal_country',
            'postal_postcode',

            'email',
            'phone_number',
            'mobile_number',
        )
        
#NOTE: may still be needed in some capacity but may warrant adjustment
class ProposalApplicantSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    ledger_id = serializers.SerializerMethodField()

    class Meta:
        model = ProposalApplicant
        fields = (
            'id',
            'last_name',
            'first_name',
            'full_name',
            'dob',

            'residential_line1',
            'residential_line2',
            'residential_line3',
            'residential_locality',
            'residential_state',
            'residential_country',
            'residential_postcode',

            'postal_same_as_residential',
            'postal_line1',
            'postal_line2',
            'postal_line3',
            'postal_locality',
            'postal_state',
            'postal_country',
            'postal_postcode',

            'email',
            'phone_number',
            'mobile_number',

            'ledger_id',
        )
    
    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_ledger_id(self, obj):
        try:
            return obj.proposal.submitter
        except:
            return


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemUserAddress
        fields = (
            'line1',
            'line2',
            'line3',
            'locality',
            'state',
            'country',
            'postcode'
        )

class UserSerializer(serializers.ModelSerializer):

    ledger_id = serializers.SerializerMethodField()
    residential_address_list = serializers.SerializerMethodField()
    postal_address_list = serializers.SerializerMethodField()
    billing_address_list = serializers.SerializerMethodField()
    is_department_user = serializers.SerializerMethodField()

    class Meta:
        model = SystemUser
        fields = (
            "ledger_id",
            "email",
            "first_name",
            "last_name",
            "legal_first_name",
            "legal_last_name",
            "title",
            "legal_dob",
            "phone_number",
            "mobile_number",
            "fax_number",
            "residential_address_list",
            "postal_address_list",
            "billing_address_list",
            "is_department_user",
        )

    def get_ledger_id(self, obj):
        if obj.ledger_id:
            return obj.ledger_id.id
        return None

    def get_residential_address_list(self, obj):
        residential_addresses = SystemUserAddress.objects.filter(address_type=SystemUserAddress.ADDRESS_TYPE[0][0],system_user=obj)
        return UserAddressSerializer(residential_addresses, many=True).data

    def get_postal_address_list(self, obj):
        postal_addresses = SystemUserAddress.objects.filter(address_type=SystemUserAddress.ADDRESS_TYPE[1][0],system_user=obj)
        return UserAddressSerializer(postal_addresses, many=True).data

    def get_billing_address_list(self, obj):
        billing_addresses = SystemUserAddress.objects.filter(address_type=SystemUserAddress.ADDRESS_TYPE[2][0],system_user=obj)
        return UserAddressSerializer(billing_addresses, many=True).data

    def get_is_department_user(self, obj):
        if obj.email:
            request = self.context["request"] if self.context else None
            if request:
                return in_dbca_domain(request)
        return False
    

#NOTE appear to be implemented, might need a minor rework
class EmailUserCommsSerializer(CommunicationLogEntrySerializer):
    # TODO: implement (?)
    documents = serializers.SerializerMethodField()
    # type = serializers.CharField(source='log_type')
    #
    class Meta:
        model = EmailUserLogEntry
    #     # fields = '__all__'
        fields = (
            'id',
            'customer',
            'to',
            'fromm',
            'cc',
            'type',
            'reference',
            'subject',
            'text',
            'created',
            'staff',
            # 'emailuser',
            'email_user_id',
            'documents',
        )
        read_only_fields = (
            'customer',
        )


# NOTE: appears to be a save serializer - remove or implement (functionality exists but may be better to use serializer)
class EmailUserLogEntrySerializer(CommunicationLogEntrySerializer):
    # TODO: implement
#     documents = serializers.SerializerMethodField()
    class Meta:
        model = EmailUserLogEntry
        fields = '__all__'
#         read_only_fields = (
#             'customer',
#         )
#
#     def get_documents(self,obj):
#         return [[d.name,d._file.url] for d in obj.documents.all()]
