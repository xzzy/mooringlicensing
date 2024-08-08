from ledger_api_client.managed_models import SystemUser, SystemUserAddress
from mooringlicensing.components.main.serializers import CommunicationLogEntrySerializer
from mooringlicensing.components.proposals.models import ProposalApplicant
from rest_framework import serializers
from mooringlicensing.components.users.models import EmailUserLogEntry
from mooringlicensing.helpers import in_dbca_domain

class UserForEndorserSerializer(serializers.ModelSerializer):

    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = SystemUser
        fields = (
            'ledger_id',
            'last_name',
            'first_name',
            'email',
            'phone_number',
            'mobile_number',
        )
    
    def get_first_name(self,obj):
        if obj.legal_first_name:
            return obj.legal_first_name
        else:
            return obj.first_name

    def get_last_name(self,obj):
        if obj.legal_first_name:
            return obj.legal_last_name
        else:
            return obj.last_name
      
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
    

#NOTE appears to be implemented, might need a minor rework
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