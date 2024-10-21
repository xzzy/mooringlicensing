from ledger_api_client.managed_models import SystemUser, SystemUserAddress
from mooringlicensing.components.main.serializers import CommunicationLogEntrySerializer
from mooringlicensing.components.proposals.models import ProposalApplicant
from rest_framework import serializers
from mooringlicensing.components.users.models import EmailUserLogEntry
from django_countries.serializer_fields import CountryField

class UserForEndorserSerializer(serializers.ModelSerializer):

    legal_first_name = serializers.SerializerMethodField()
    legal_last_name = serializers.SerializerMethodField()

    class Meta:
        model = SystemUser
        fields = (
            'ledger_id',
            'legal_last_name',
            'legal_first_name',
            'email',
            'phone_number',
            'mobile_number',
        )
    
    def get_legal_first_name(self,obj):
        if obj.legal_first_name:
            return obj.legal_first_name
        else:
            return obj.first_name

    def get_legal_last_name(self,obj):
        if obj.legal_first_name:
            return obj.legal_last_name
        else:
            return obj.last_name
      

class ProposalApplicantSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    ledger_id = serializers.SerializerMethodField()
    residential_country = CountryField()
    postal_country = CountryField()

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
            return obj.proposal.proposal_applicant.email_user_id
        except:
            return


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemUserAddress
        fields = (
            'id',
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

    class Meta:
        model = SystemUser
        fields = (
            "id",
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
    

class EmailUserCommsSerializer(CommunicationLogEntrySerializer):

    documents = serializers.SerializerMethodField()

    class Meta:
        model = EmailUserLogEntry
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
            'email_user_id',
            'documents',
        )
        read_only_fields = (
            'customer',
        )