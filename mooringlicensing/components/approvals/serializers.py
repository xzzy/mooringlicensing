from django.conf import settings
from ledger.accounts.models import EmailUser,Address

from mooringlicensing.components.main import serializers
from mooringlicensing.components.proposals.serializers import ProposalSerializer, InternalProposalSerializer
#from mooringlicensing.components.main.serializers import ApplicationTypeSerializer
from mooringlicensing.components.approvals.models import (
    Approval,
    ApprovalLogEntry,
    ApprovalUserAction, DcvOrganisation, DcvVessel
)
from mooringlicensing.components.organisations.models import (
    Organisation
)
from mooringlicensing.components.main.serializers import CommunicationLogEntrySerializer
from mooringlicensing.components.proposals.serializers import ProposalSerializer
from rest_framework import serializers

class EmailUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = ('id','email','first_name','last_name','title','organisation')

class ApprovalPaymentSerializer(serializers.ModelSerializer):
    org_applicant = serializers.SerializerMethodField(read_only=True)
    bpay_allowed = serializers.SerializerMethodField(read_only=True)
    monthly_invoicing_allowed = serializers.SerializerMethodField(read_only=True)
    other_allowed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Approval
        fields = (
            'lodgement_number',
            'current_proposal',
            'expiry_date',
            'org_applicant',
            'bpay_allowed',
            'monthly_invoicing_allowed',
            'other_allowed',
        )
        read_only_fields = (
            'lodgement_number',
            'current_proposal',
            'expiry_date',
            'org_applicant',
            'bpay_allowed',
            'monthly_invoicing_allowed',
            'other_allowed',
        )

    def get_org_applicant(self,obj):
        return obj.org_applicant.name if obj.org_applicant else None

    def get_bpay_allowed(self,obj):
        return obj.bpay_allowed

    def get_monthly_invoicing_allowed(self,obj):
        return obj.monthly_invoicing_allowed

    def get_other_allowed(self,obj):
        return settings.OTHER_PAYMENT_ALLOWED


class _ApprovalPaymentSerializer(serializers.ModelSerializer):
    applicant = serializers.SerializerMethodField(read_only=True)
    applicant_type = serializers.SerializerMethodField(read_only=True)
    applicant_id = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source='get_status_display')
    title = serializers.CharField(source='current_proposal.title')
    application_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Approval
        fields = (
            'id',
            'lodgement_number',
            'current_proposal',
            'title',
            'issue_date',
            'start_date',
            'expiry_date',
            'applicant',
            'applicant_type',
            'applicant_id',
            'status',
            'cancellation_date',
            'application_type',
        )

    def get_application_type(self,obj):
        if obj.current_proposal.application_type:
            return obj.current_proposal.application_type.name
        return None

    def get_applicant(self,obj):
        return obj.applicant.name if isinstance(obj.applicant, Organisation) else obj.applicant

    def get_applicant_type(self,obj):
        return obj.applicant_type

    def get_applicant_id(self,obj):
        return obj.applicant_id


class DcvOrganisationSerializer(serializers.ModelSerializer):
    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not data['name']:
            field_errors['name'] = ['Please enter organisation name.',]
        if not data['abn']:
            field_errors['abn'] = ['Please enter ABN / ACN.',]

        # Raise errors
        if field_errors:
            raise serializers.ValidationError(field_errors)
        if non_field_errors:
            raise serializers.ValidationError(non_field_errors)

        return data

    class Meta:
        model = DcvOrganisation
        fields = (
            'id',
            'name',
            'abn',
        )
        read_only_fields = (
            'id',
        )


class DcvVesselSerializer(serializers.ModelSerializer):
    dcv_organisation_id = serializers.IntegerField()

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not data['rego_no']:
            field_errors['rego_no'] = ['Please enter vessel rego_no.',]
        if not data['vessel_name']:
            field_errors['vessel_name'] = ['Please enter vessel name.',]
        if not data['uiv_vessel_identifier']:
            field_errors['uiv_vessel_identifier'] = ['Please enter UIV vessel identifier.',]
        if not data['dcv_organisation_id']:
            field_errors['dcv_organisation_id'] = ['Please enter organisation and/or ABN / ACN.',]

        # Raise errors
        if field_errors:
            raise serializers.ValidationError(field_errors)
        if non_field_errors:
            raise serializers.ValidationError(non_field_errors)

        return data

    class Meta:
        model = DcvVessel
        fields = (
            'id',
            'vessel_name',
            'rego_no',
            'uiv_vessel_identifier',
            'dcv_organisation_id',
        )
        read_only_fields = (
            'id',
        )


class ApprovalSerializer(serializers.ModelSerializer):
    applicant = serializers.SerializerMethodField(read_only=True)
    applicant_type = serializers.SerializerMethodField(read_only=True)
    applicant_id = serializers.SerializerMethodField(read_only=True)
    licence_document = serializers.CharField(source='licence_document._file.url')
    renewal_document = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source='get_status_display')
    allowed_assessors = EmailUserSerializer(many=True)
    title = serializers.CharField(source='current_proposal.title')
    application_type = serializers.SerializerMethodField(read_only=True)
    linked_applications = serializers.SerializerMethodField(read_only=True)
    can_renew = serializers.SerializerMethodField()
    can_extend = serializers.SerializerMethodField()
    is_assessor = serializers.SerializerMethodField()
    is_approver = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = (
            'id',
            'lodgement_number',
            'linked_applications',
            'licence_document',
            'replaced_by',
            'current_proposal',
            'title',
            'renewal_document',
            'renewal_sent',
            'issue_date',
            'original_issue_date',
            'start_date',
            'expiry_date',
            'surrender_details',
            'suspension_details',
            'applicant',
            'applicant_type',
            'applicant_id',
            'extracted_fields',
            'status',
            'reference',
            'can_reissue',
            'allowed_assessors',
            'cancellation_date',
            'cancellation_details',
            'can_action',
            'set_to_cancel',
            'set_to_surrender',
            'set_to_suspend',
            'can_renew',
            'can_extend',
            'can_amend',
            'can_reinstate',
            'application_type',
            'migrated',
            'is_assessor',
            'is_approver',
            #'can_reissue_lawful_authority',
            #'is_lawful_authority',
            #'is_lawful_authority_finalised',
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data' defined are requested from the serializer. We
        # also require the following additional fields for some of the mRender functions
        datatables_always_serialize = (
            'id',
            'title',
            'status',
            'reference',
            'lodgement_number',
            'linked_applications',
            'licence_document',
            'start_date',
            'expiry_date',
            'applicant',
            'can_reissue',
            'can_action',
            'can_reinstate',
            'can_amend',
            'can_renew',
            'can_extend',
            'set_to_cancel',
            'set_to_suspend',
            'set_to_surrender',
            'current_proposal',
            'renewal_document',
            'renewal_sent',
            'allowed_assessors',
            'application_type',
            'migrated',
            'is_assessor',
            'is_approver',
            #'can_reissue_lawful_authority',
            #'is_lawful_authority',
            #'is_lawful_authority_finalised',
        )

    def get_linked_applications(self,obj):
        return obj.linked_applications


    def get_renewal_document(self,obj):
        if obj.renewal_document and obj.renewal_document._file:
            return obj.renewal_document._file.url
        return None

    def get_application_type(self,obj):
        if obj.current_proposal.application_type:
            return obj.current_proposal.application_type.name
        return None

    def get_applicant(self,obj):
        try:
            return obj.applicant.name if isinstance(obj.applicant, Organisation) else obj.applicant
        except:
            return None

    def get_applicant_type(self,obj):
        try:
            return obj.applicant_type
        except:
            return None

    def get_applicant_id(self,obj):
        try:
            return obj.applicant_id
        except:
            return None

    def get_can_renew(self,obj):
        return obj.can_renew

    def get_can_extend(self,obj):
        return obj.can_extend

    def get_is_assessor(self,obj):
        request = self.context['request']
        user = request.user
        return obj.is_assessor(user)

    def get_is_approver(self,obj):
        request = self.context['request']
        user = request.user
        return obj.is_approver(user)

class ApprovalExtendSerializer(serializers.Serializer):
    extend_details = serializers.CharField()

class ApprovalCancellationSerializer(serializers.Serializer):
    cancellation_date = serializers.DateField(input_formats=['%d/%m/%Y'])
    cancellation_details = serializers.CharField()

class ApprovalSuspensionSerializer(serializers.Serializer):
    from_date = serializers.DateField(input_formats=['%d/%m/%Y'])
    to_date = serializers.DateField(input_formats=['%d/%m/%Y'], required=False, allow_null=True)
    suspension_details = serializers.CharField()

class ApprovalSurrenderSerializer(serializers.Serializer):
    surrender_date = serializers.DateField(input_formats=['%d/%m/%Y'])
    surrender_details = serializers.CharField()

class ApprovalUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')
    class Meta:
        model = ApprovalUserAction
        fields = '__all__'

class ApprovalLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()
    class Meta:
        model = ApprovalLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]


class ListApprovalSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    approval_type_dict = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = (
            'id',
            'lodgement_number',
            'status',
            'approval_type_dict',
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data' defined are requested from the serializer. We
        # also require the following additional fields for some of the mRender functions
        datatables_always_serialize = (
            'id',
            'lodgement_number',
            'status',
            'approval_type_dict',
        )

    def get_status(self, obj):
        return obj.get_status_display()

    def get_approval_type_dict(self, obj):
        return {
            'code': obj.child_obj.code,
            'description': obj.child_obj.description,
        }
