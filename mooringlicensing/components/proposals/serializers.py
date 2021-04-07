from django.conf import settings
from ledger.accounts.models import EmailUser,Address
#from mooringlicensing.components.main.models import ApplicationType
from mooringlicensing.components.proposals.models import (
                                    #ProposalType,
                                    Proposal,
                                    ProposalUserAction,
                                    ProposalLogEntry,
                                    #Referral,
                                    ProposalRequirement,
                                    ProposalStandardRequirement,
                                    ProposalDeclinedDetails,
                                    AmendmentRequest,
                                    AmendmentReason,
                                    #ProposalApplicantDetails,
                                    #ProposalActivitiesLand,
                                    #ProposalActivitiesMarine,
                                    #ProposalPark,
                                    #ProposalParkActivity,
                                    #Vehicle,
                                    #Vessel,
                                    #ProposalTrail,
                                    #QAOfficerReferral,
                                    #ProposalParkAccess,
                                    #ProposalTrailSection,
                                    #ProposalTrailSectionActivity,
                                    #ProposalParkZoneActivity,
                                    #ProposalParkZone,
                                    #ProposalOtherDetails,
                                    #ProposalAccreditation,
                                    ChecklistQuestion,
                                    ProposalAssessmentAnswer,
                                    ProposalAssessment,
                                    RequirementDocument,
                                    #DistrictProposal,
                                    #DistrictProposalDeclinedDetails,
                                    VesselDetails,
                                    VesselOwnership,
                                    Vessel,
                                    MooringBay,
                                )
from mooringlicensing.components.organisations.models import (
                                Organisation
                            )
from mooringlicensing.components.main.serializers import CommunicationLogEntrySerializer
from mooringlicensing.components.organisations.serializers import OrganisationSerializer
from mooringlicensing.components.users.serializers import UserAddressSerializer, DocumentSerializer
from rest_framework import serializers
from django.db.models import Q
from reversion.models import Version


class EmailUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = ('id','email','first_name','last_name','title','organisation')

class EmailUserAppViewSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    #identification = DocumentSerializer()

    class Meta:
        model = EmailUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'dob',
                  'title',
                  'organisation',
                  'residential_address',
                  #'identification',
                  'email',
                  'phone_number',
                  'mobile_number',)

#class ProposalApplicantDetailsSerializer(serializers.ModelSerializer):
 #   class Meta:
  #      model = ProposalApplicantDetails
   #     fields = ('id','first_name')

#class ProposalAccreditationSerializer(serializers.ModelSerializer):
#    accreditation_type_value= serializers.SerializerMethodField()
#    accreditation_expiry = serializers.DateField(format="%d/%m/%Y",input_formats=['%d/%m/%Y'],required=False,allow_null=True)
#
#    class Meta:
#        model = ProposalAccreditation
#        #fields = '__all__'
#        fields=('id',
#                'accreditation_type',
#                'accreditation_expiry',
#                'comments',
#                'proposal_other_details',
#                'accreditation_type_value'
#                )
#
#    def get_accreditation_type_value(self,obj):
#        return obj.get_accreditation_type_display()


#class ProposalOtherDetailsSerializer(serializers.ModelSerializer):
#    nominated_start_date = serializers.DateField(format="%d/%m/%Y",input_formats=['%d/%m/%Y'],required=False,allow_null=True)
#    insurance_expiry = serializers.DateField(format="%d/%m/%Y",input_formats=['%d/%m/%Y'],required=False,allow_null=True)
#    accreditations = ProposalAccreditationSerializer(many=True, read_only=True)
#    preferred_licence_period = serializers.CharField(allow_blank=True, allow_null=True)
#    proposed_end_date = serializers.DateField(format="%d/%m/%Y",read_only=True)
#
#    class Meta:
#        model = ProposalOtherDetails
#        fields=(
#                'id',
#                'accreditations',
#                'preferred_licence_period',
#                'nominated_start_date',
#                'insurance_expiry',
#                'other_comments',
#                'credit_fees',
#                'credit_docket_books',
#                'docket_books_number',
#                'mooring',
#                'proposed_end_date',
#                )


#class SaveProposalOtherDetailsSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = ProposalOtherDetails
#        fields=(
#                'preferred_licence_period',
#                'nominated_start_date',
#                'insurance_expiry',
#                'other_comments',
#                'credit_fees',
#                'credit_docket_books',
#                'proposal',
#                )


class ChecklistQuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChecklistQuestion
        #fields = '__all__'
        fields=('id',
                'text',
                'answer_type',
                )
class ProposalAssessmentAnswerSerializer(serializers.ModelSerializer):
    question=ChecklistQuestionSerializer(read_only=True)
    class Meta:
        model = ProposalAssessmentAnswer
        fields = ('id',
                'question',
                'answer',
                'text_answer',
                )

class ProposalAssessmentSerializer(serializers.ModelSerializer):
    checklist=serializers.SerializerMethodField()

    class Meta:
        model = ProposalAssessment
        fields = ('id',
                'completed',
                'submitter',
                'referral_assessment',
                'referral_group',
                'referral_group_name',
                'checklist'
                )

    def get_checklist(self,obj):
        qs= obj.checklist.order_by('question__order')
        return ProposalAssessmentAnswerSerializer(qs, many=True, read_only=True).data


class BaseProposalSerializer(serializers.ModelSerializer):
    readonly = serializers.SerializerMethodField(read_only=True)
    documents_url = serializers.SerializerMethodField()
    # proposal_type = serializers.SerializerMethodField()
    allowed_assessors = EmailUserSerializer(many=True)
    submitter = EmailUserSerializer()
    other_details = serializers.SerializerMethodField()

    get_history = serializers.ReadOnlyField()
    # fee_invoice_url = serializers.SerializerMethodField()
    application_type_code = serializers.SerializerMethodField()
    application_type_text = serializers.SerializerMethodField()
    application_type_dict = serializers.SerializerMethodField()
    editable_vessel = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                #'application_type',
                'application_type_code',
                'application_type_text',
                'application_type_dict',
                'proposal_type',
                # 'activity',
                'approval_level',
                'title',
                'customer_status',
                'processing_status',
                #'review_status',
                'applicant_type',
                'applicant',
                #'org_applicant',
                #'proxy_applicant',
                'submitter',
                'assigned_officer',
                #'previous_application',
                'get_history',
                'lodgement_date',
                'modified_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'documents_url',
                #'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'allowed_assessors',
                'pending_amendment_request',
                'is_amendment_proposal',
                # tab field models
                'applicant_details',
                # 'fee_invoice_url',
                'fee_paid',
                ## vessel fields
                'rego_no',
                'vessel_id',
                'vessel_details_id', 
                'vessel_ownership_id', 
                'vessel_type',
                'vessel_name',
                'vessel_overall_length',
                'vessel_length',
                'vessel_draft',
                'vessel_beam',
                'vessel_weight',
                'berth_mooring',
                'org_name',
                'percentage',
                'editable_vessel',
                'individual_owner',
                'insurance_choice',
                'preferred_bay_id',
                'silent_elector',
                )
        read_only_fields=('documents',)

    def get_editable_vessel(self, obj):
        return obj.editable_vessel

    def get_application_type_code(self, obj):
        return obj.application_type_code

    def get_application_type_text(self, obj):
        return obj.child_obj.description

    def get_application_type_dict(self, obj):
        return {
            'code': obj.child_obj.code,
            'description': obj.child_obj.description,
        }

    def get_documents_url(self,obj):
        return '/media/{}/proposals/{}/documents/'.format(settings.MEDIA_APP_DIR, obj.id)

    def get_readonly(self,obj):
        return False

    def get_processing_status(self,obj):
        return obj.get_processing_status_display()

    #def get_review_status(self,obj):
     #   return obj.get_review_status_display()

    def get_customer_status(self,obj):
        return obj.get_customer_status_display()

    # def get_proposal_type(self,obj):
    #     return obj.get_proposal_type_display()
    #     return obj.

    # def get_fee_invoice_url(self,obj):
    #     return '/cols/payments/invoice-pdf/{}'.format(obj.fee_invoice_reference) if obj.fee_paid else None

    def get_fee_invoice_references(self, obj):
        ret_list = []
        if obj.application_fees.count():
            for application_fee in obj.application_fees.all():
                ret_list.append(application_fee.invoice_reference)
        return ret_list


class ListProposalSerializer(BaseProposalSerializer):
    submitter = EmailUserSerializer()
    applicant = serializers.CharField(read_only=True)
    processing_status = serializers.SerializerMethodField()
    # review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField()
    assigned_officer = serializers.SerializerMethodField()
    application_type_dict = serializers.SerializerMethodField()

    # application_type = serializers.CharField(source='application_type.name', read_only=True)
    assessor_process = serializers.SerializerMethodField()
    # fee_invoice_url = serializers.SerializerMethodField()
    fee_invoice_references = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                # 'application_type',
                'application_type_dict',
                'proposal_type',
                # 'activity',
                # 'approval_level',
                # 'title',
                'customer_status',
                'processing_status',
                # 'review_status',
                'applicant',
                # 'proxy_applicant',
                'submitter',
                'assigned_officer',
                # 'previous_application',
                # 'get_history',
                'lodgement_date',
                # 'modified_date',
                # 'readonly',
                'can_user_edit',
                'can_user_view',
                # 'reference',
                'lodgement_number',
                # 'lodgement_sequence',
                # 'can_officer_process',
                'assessor_process',
                # 'allowed_assessors',
                # 'proposal_type',
                # 'fee_invoice_url',
                'fee_invoice_references',
                # 'fee_paid',
                # 'aho',
                )
        # the serverSide functionality of datatables is such that only columns that have field 'data' defined are requested from the serializer. We
        # also require the following additional fields for some of the mRender functions
        datatables_always_serialize = (
                # 'id',
                'proposal_type',
                # 'activity',
                # 'title',
                'customer_status',
                'application_type_dict',
                # 'processing_status',
                # 'applicant',
                # 'submitter',
                # 'assigned_officer',
                'lodgement_date',
                'can_user_edit',
                'can_user_view',
                # 'reference',
                'lodgement_number',
                # 'can_officer_process',
                'assessor_process',
                # 'allowed_assessors',
                # 'fee_invoice_url',
                'fee_invoice_references',
                # 'fee_paid',
                )

    def get_assigned_officer(self,obj):
        if obj.assigned_officer:
            return obj.assigned_officer.get_full_name()
        return None

    def get_assessor_process(self,obj):
        # Check if currently logged in user has access to process the proposal
        request = self.context['request']
        user = request.user
        if obj.can_officer_process:
            '''if (obj.assigned_officer and obj.assigned_officer == user) or (user in obj.allowed_assessors):
                return True'''
            if obj.assigned_officer:
                if obj.assigned_officer == user:
                    return True
            elif user in obj.allowed_assessors:
                return True
        return False


class ProposalSerializer(BaseProposalSerializer):
    #submitter = serializers.CharField(source='submitter.get_full_name')
    processing_status = serializers.SerializerMethodField(read_only=True)
    #review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)

    #application_type = serializers.CharField(source='application_type.name', read_only=True)

    def get_readonly(self,obj):
        return obj.can_user_view


class SaveProposalSerializer(BaseProposalSerializer):
    #assessor_data = serializers.JSONField(required=False)
    preferred_bay_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Proposal
        fields = (
                'id',
                'insurance_choice',
                'preferred_bay_id',
                'silent_elector',
                )
        read_only_fields=('id',)


class SaveDraftProposalVesselSerializer(serializers.ModelSerializer):

    class Meta:
        model = Proposal
        fields = (
                'rego_no',
                'vessel_id',
                #'vessel_details_id', 
                #'vessel_ownership_id', 
                'vessel_type',
                'vessel_name',
                'vessel_overall_length',
                'vessel_length',
                'vessel_draft',
                'vessel_beam',
                'vessel_weight',
                'berth_mooring',
                'org_name',
                'percentage',
                'individual_owner',
                )


## TODO: rename to Org applicant?
#class ApplicantSerializer(serializers.ModelSerializer):
#    from mooringlicensing.components.organisations.serializers import OrganisationAddressSerializer
#    address = OrganisationAddressSerializer(read_only=True)
#    class Meta:
#        model = Organisation
#        fields = (
#                    'id',
#                    'name',
#                    'abn',
#                    'address',
#                    'email',
#                    'phone_number',
#                )


class ProposalDeclinedDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalDeclinedDetails
        fields = '__all__'


class InternalProposalSerializer(BaseProposalSerializer):
    applicant = serializers.CharField(read_only=True)
    #org_applicant = OrganisationSerializer()
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    submitter = EmailUserAppViewSerializer()
    proposaldeclineddetails = ProposalDeclinedDetailsSerializer()
    assessor_mode = serializers.SerializerMethodField()
    can_edit_activities = serializers.SerializerMethodField()
    can_edit_period = serializers.SerializerMethodField()
    current_assessor = serializers.SerializerMethodField()
    assessor_data = serializers.SerializerMethodField()
    allowed_assessors = EmailUserSerializer(many=True)
    approval_level_document = serializers.SerializerMethodField()
    application_type = serializers.CharField(source='application_type.name', read_only=True)
    region = serializers.CharField(source='region.name', read_only=True)
    district = serializers.CharField(source='district.name', read_only=True)
    reversion_ids = serializers.SerializerMethodField()
    assessor_assessment=ProposalAssessmentSerializer(read_only=True)
    referral_assessments=ProposalAssessmentSerializer(read_only=True, many=True)
    fee_invoice_url = serializers.SerializerMethodField()
    requirements_completed=serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                'activity',
                'approval_level',
                'approval_level_document',
                'region',
                'district',
                'tenure',
                'title',
                'data',
                'schema',
                'customer_status',
                'processing_status',
                'review_status',
                'applicant',
                'org_applicant',
                'proxy_applicant',
                'submitter',
                'applicant_type',
                'assigned_officer',
                'assigned_approver',
                'previous_application',
                'get_history',
                'lodgement_date',
                'modified_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'documents_url',
                'assessor_mode',
                'current_assessor',
                'assessor_data',
                'comment_data',
                'allowed_assessors',
                'proposed_issuance_approval',
                'proposed_decline_status',
                'proposaldeclineddetails',
                'permit',
                'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'proposal_type',
                'applicant_details',
                'other_details',
                'activities_land',
                'land_access',
                'land_access',
                'trail_activities',
                'trail_section_activities',
                'activities_marine',
                'training_completed',
                'can_edit_activities',
                'can_edit_period',
                'reversion_ids',
                'assessor_assessment',
                'referral_assessments',
                'fee_invoice_url',
                'fee_paid',
                'requirements_completed'
                )
        read_only_fields=('documents','requirements')

    def get_approval_level_document(self,obj):
        if obj.approval_level_document is not None:
            return [obj.approval_level_document.name,obj.approval_level_document._file.url]
        else:
            return obj.approval_level_document

    def get_assessor_mode(self,obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return {
            'assessor_mode': True,
            'has_assessor_mode': obj.has_assessor_mode(user),
            'assessor_can_assess': obj.can_assess(user),
            'assessor_level': 'assessor',
            'assessor_box_view': obj.assessor_comments_view(user)
        }

    def get_can_edit_activities(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_edit_activities(user)

    def get_can_edit_period(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_edit_period(user)

    def get_readonly(self,obj):
        return True

    def get_requirements_completed(self,obj):
        return True

    def get_current_assessor(self,obj):
        return {
            'id': self.context['request'].user.id,
            'name': self.context['request'].user.get_full_name(),
            'email': self.context['request'].user.email
        }

    def get_assessor_data(self,obj):
        return obj.assessor_data

    def get_reversion_ids(self,obj):
        return obj.reversion_ids[:5]

    def get_fee_invoice_url(self,obj):
        return '/cols/payments/invoice-pdf/{}'.format(obj.fee_invoice_reference) if obj.fee_paid else None


class ProposalUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')
    class Meta:
        model = ProposalUserAction
        fields = '__all__'

class ProposalLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()
    class Meta:
        model = ProposalLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]


class RequirementDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequirementDocument
        fields = ('id', 'name', '_file')
        #fields = '__all__'

class ProposalRequirementSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(input_formats=['%d/%m/%Y'],required=False,allow_null=True)
    can_referral_edit=serializers.SerializerMethodField()
    can_district_assessor_edit=serializers.SerializerMethodField()
    requirement_documents = RequirementDocumentSerializer(many=True, read_only=True)
    class Meta:
        model = ProposalRequirement
        fields = (
            'id',
            'due_date',
            'free_requirement',
            'standard_requirement',
            'standard','order',
            'proposal',
            'recurrence',
            'recurrence_schedule',
            'recurrence_pattern',
            'requirement',
            'is_deleted',
            'copied_from',
            'referral_group',
            'can_referral_edit',
            'district_proposal',
            'district',
            'requirement_documents',
            'can_district_assessor_edit',
            'require_due_date',
            'copied_for_renewal',
        )
        read_only_fields = ('order','requirement', 'copied_from')

    def get_can_referral_edit(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_referral_edit(user)

    def get_can_district_assessor_edit(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_district_assessor_edit(user)

class ProposalStandardRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalStandardRequirement
        fields = ('id','code','text')

class ProposedApprovalSerializer(serializers.Serializer):
    expiry_date = serializers.DateField(input_formats=['%d/%m/%Y'])
    start_date = serializers.DateField(input_formats=['%d/%m/%Y'])
    details = serializers.CharField()
    cc_email = serializers.CharField(required=False,allow_null=True)

class PropedDeclineSerializer(serializers.Serializer):
    reason = serializers.CharField()
    cc_email = serializers.CharField(required=False, allow_null=True)

class OnHoldSerializer(serializers.Serializer):
    comment = serializers.CharField()

#
#class VesselSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Vessel
#        fields = '__all__'

class AmendmentRequestSerializer(serializers.ModelSerializer):
    #reason = serializers.SerializerMethodField()

    class Meta:
        model = AmendmentRequest
        fields = '__all__'

    #def get_reason (self,obj):
        #return obj.get_reason_display()
        #return obj.reason.reason

class AmendmentRequestDisplaySerializer(serializers.ModelSerializer):
    reason = serializers.SerializerMethodField()

    class Meta:
        model = AmendmentRequest
        fields = '__all__'

    def get_reason (self,obj):
        #return obj.get_reason_display()
        return obj.reason.reason if obj.reason else None


class SearchKeywordSerializer(serializers.Serializer):
    number = serializers.CharField()
    id = serializers.IntegerField()
    type = serializers.CharField()
    applicant = serializers.CharField()
    #text = serializers.CharField(required=False,allow_null=True)
    text = serializers.JSONField(required=False)

class SearchReferenceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()

#class ApplicationTypeDescriptionsSerializer(serializers.Serializer):
#    descriptions = serializers.SerializerMethodField()
#
#    def get_descriptions(self, obj):
#        return Proposal.application_type_descriptions


class VesselSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vessel
        fields = '__all__'


class VesselDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = VesselDetails
        fields = '__all__'


class SaveVesselDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = VesselDetails
        fields = (
                'vessel_type',
                'vessel', # link to rego number
                'vessel_name', 
                'vessel_overall_length',
                'vessel_length',
                'vessel_draft',
                'vessel_weight',
                'berth_mooring',
                #status
                #exported
                )


class VesselOwnershipSerializer(serializers.ModelSerializer):

    class Meta:
        model = VesselOwnership
        fields = '__all__'


class SaveVesselOwnershipSerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(max_length=200, allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = VesselOwnership
        fields = (
                'owner',
                'vessel',
                'percentage',
                'org_name',
                #'editable',
                'start_date',
                'end_date',
                )

class MooringBaySerializer(serializers.ModelSerializer):

    class Meta:
        model = MooringBay
        fields = '__all__'


