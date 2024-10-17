import os
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, TemplateView
from mooringlicensing import settings

from mooringlicensing.components.proposals.models import (
    ElectoralRollDocument, HullIdentificationNumberDocument, 
    InsuranceCertificateDocument, ProofOfIdentityDocument, Proposal,
    AuthorisedUserApplication, Mooring, 
    MooringLicenceApplication, SignedLicenceAgreementDocument, 
    VesselRegistrationDocument, WrittenProofDocument,
    ProposalSiteLicenseeMooringRequest,
)

from mooringlicensing.components.approvals.models import (
    Approval, ApprovalDocument, ApprovalLogDocument, 
    AuthorisedUserSummaryDocument, DcvAdmissionDocument, 
    DcvPermitDocument, RenewalDocument, 
    WaitingListOfferDocument,
)

from rest_framework.views import APIView
import logging
from mooringlicensing.components.proposals.utils import get_file_content_http_response

from mooringlicensing.settings import PRIVATE_MEDIA_STORAGE_LOCATION

logger = logging.getLogger(__name__)

#TODO replace/remove
#class ProposalHistoryCompareView(HistoryCompareDetailView):
#    """
#    View for reversion_compare
#    """
#    model = Proposal
#    template_name = 'mooringlicensing/reversion_history.html'

#TODO replace/remove
#class ProposalFilteredHistoryCompareView(HistoryCompareDetailView):
#    """
#    View for reversion_compare - with 'status' in the comment field only'
#    """
#    model = Proposal
#    template_name = 'mooringlicensing/reversion_history.html'
#
#    def _get_action_list(self,):
#        """ Get only versions when processing_status changed, and add the most recent (current) version """
#        current_revision_id = Version.objects.get_for_object(self.get_object()).first().revision_id
#        action_list = [
#            {"version": version, "revision": version.revision}
#            for version in self._order_version_queryset(
#                Version.objects.get_for_object(self.get_object()).select_related("revision__user").filter(Q(revision__comment__icontains='status') | Q(revision_id=current_revision_id))
#            )
#        ]
#        return action_list

#TODO replace/remove
#class ApprovalHistoryCompareView(HistoryCompareDetailView):
#    """
#    View for reversion_compare
#    """
#    model = Approval
#    template_name = 'mooringlicensing/reversion_history.html'

#TODO replace/remove
#class ComplianceHistoryCompareView(HistoryCompareDetailView):
#    """
#    View for reversion_compare
#    """
#    model = Compliance
#    template_name = 'mooringlicensing/reversion_history.html'


class TestEmailView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Test Email Script Completed')


class MooringLicenceApplicationDocumentsUploadView(TemplateView):
    template_name = 'mooringlicensing/proposals/mooring_licence_application_documents_upload.html'

    def get_object(self):
        return get_object_or_404(MooringLicenceApplication, uuid=self.kwargs['uuid_str'])

    def get(self, request, *args, **kwargs):
        proposal = self.get_object()

        #TODO add auth check here (and other TemplateView functions)

        debug = self.request.GET.get('debug', 'f') #TODO use actual debug (if even needed)
        if debug.lower() in ['true', 't', 'yes', 'y']:
            debug = True
        else:
            debug = False

        #TODO handle this better or elsewhere
        if not proposal.processing_status == Proposal.PROCESSING_STATUS_AWAITING_DOCUMENTS:
            if not debug:
                raise ValidationError('You cannot upload documents for the application when it is not in awaiting-documents status')

        context = {
            'proposal': proposal,
            'dev': settings.DEV_STATIC,
            'dev_url': settings.DEV_STATIC_URL
        }

        if hasattr(settings, 'DEV_APP_BUILD_URL') and settings.DEV_APP_BUILD_URL:
            context['app_build_url'] = settings.DEV_APP_BUILD_URL

        return render(request, self.template_name, context)


class AuthorisedUserApplicationEndorseView(TemplateView):

    def get_object(self):
        return get_object_or_404(AuthorisedUserApplication, uuid=self.kwargs['uuid_str'])

    def get(self, request, *args, **kwargs):
        proposal = self.get_object()
        mooring_name = request.GET.get("mooring_name","")
        
        if not proposal.processing_status == Proposal.PROCESSING_STATUS_AWAITING_ENDORSEMENT:
            raise ValidationError('You cannot endorse/decline the application not in awaiting-endorsement status')
        
        # checking if the user holds an active mooring licence for the specified mooring
        try:
            mooring_status =  Mooring.objects.filter(
                mooring_licence__approval__current_proposal__proposal_applicant__email_user_id=request.user.id, 
                name=mooring_name,
                mooring_licence__status="current")
        except Exception as e:
            raise ValidationError('There is no mooring licence for this mooring')
        if(not mooring_status.exists()):
            raise ValidationError('You do not hold an active mooring site licence to endorse/decline the application')
        
        #get ProposalSiteLicenseeMooringRequest
        site_licensee_mooring_request = ProposalSiteLicenseeMooringRequest.objects.filter(proposal=proposal,
                                                          mooring__name=mooring_name,
                                                          site_licensee_email=request.user.email,
                                                          enabled=True)
        if not site_licensee_mooring_request.exists():
            raise ValidationError('No valid site licensee mooring request for site licensee, mooring, and proposal set')

        action = self.kwargs['action']
        if action == 'endorse':
            self.template_name = 'mooringlicensing/proposals/authorised_user_application_endorsed.html'
            site_licensee_mooring_request.first().endorse_approved(request)
        elif action == 'decline':
            self.template_name = 'mooringlicensing/proposals/authorised_user_application_declined.html'
            site_licensee_mooring_request.first().endorse_declined(request)
        proposal.refresh_from_db()

        context = {
            'proposal': proposal,
            'mooring': proposal.mooring,
        }

        return render(request, self.template_name, context)

class VesselRegistrationDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = VesselRegistrationDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response


class HullIdentificationNumberDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = HullIdentificationNumberDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response


class ElectoralRollDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = ElectoralRollDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response


class InsuranceCertificateDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = InsuranceCertificateDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response

class WrittenProofDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = WrittenProofDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response

class SignedLicenceAgreementDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = SignedLicenceAgreementDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response

class ProofOfIdentityDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = ProofOfIdentityDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response

class WaitingListOfferDocumentView(APIView):

    def get(self, request,  approval_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = WaitingListOfferDocument.relative_path_to_file(approval_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response


class ApprovalDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = ApprovalDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response


class AuthorisedUserSummaryDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = AuthorisedUserSummaryDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response


class RenewalDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = RenewalDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response


class ApprovalLogDocumentView(APIView):

    def get(self, request,  proposal_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = ApprovalLogDocument.relative_path_to_file(proposal_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response


class DcvAdmissionDocumentView(APIView):

    def get(self, request,  dcv_admission_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = DcvAdmissionDocument.relative_path_to_file(dcv_admission_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response


class DcvPermitDocumentView(APIView):

    def get(self, request,  dcv_permit_id, filename):
        response = None

        ### Permission rules
        allow_access = True
        ###

        if allow_access:
            file_path = DcvPermitDocument.relative_path_to_file(dcv_permit_id, filename)
            file_path = os.path.join(PRIVATE_MEDIA_STORAGE_LOCATION, file_path)
            response = get_file_content_http_response(file_path)

        return response