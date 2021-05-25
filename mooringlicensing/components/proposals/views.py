from django.http import HttpResponse,JsonResponse
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView
from django.db.models import Q
# from mooringlicensing.components.proposals.utils import create_data_from_form
from mooringlicensing.components.proposals.models import (Proposal,  # Referral,
    # ProposalType,
                                                          HelpPage, AuthorisedUserApplication, Mooring
                                                          )
from mooringlicensing.components.approvals.models import Approval
from mooringlicensing.components.compliances.models import Compliance
import json,traceback
from reversion_compare.views import HistoryCompareDetailView
from reversion.models import Version

class ProposalView(TemplateView):
    template_name = 'mooringlicensing/proposal.html'

    def post(self, request, *args, **kwargs):
        extracted_fields = []
        try:
            proposal_id = request.POST.pop('proposal_id')
            proposal = Proposal.objects.get(proposal_id)
            schema = json.loads(request.POST.pop('schema')[0])
            extracted_fields = create_data_from_form(schema,request.POST, request.FILES)
            proposal.schema = schema;
            proposal.data = extracted_fields
            proposal.save()
            return redirect(reverse('external'))
        except:
            traceback.print_exc
            return JsonResponse({error:"something went wrong"},safe=False,status=400)


class ProposalHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Proposal
    template_name = 'mooringlicensing/reversion_history.html'


class ProposalFilteredHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare - with 'status' in the comment field only'
    """
    model = Proposal
    template_name = 'mooringlicensing/reversion_history.html'

    def _get_action_list(self,):
        """ Get only versions when processing_status changed, and add the most recent (current) version """
        current_revision_id = Version.objects.get_for_object(self.get_object()).first().revision_id
        action_list = [
            {"version": version, "revision": version.revision}
            for version in self._order_version_queryset(
                #Version.objects.get_for_object(self.get_object()).select_related("revision__user").filter(revision__comment__icontains='status')
                Version.objects.get_for_object(self.get_object()).select_related("revision__user").filter(Q(revision__comment__icontains='status') | Q(revision_id=current_revision_id))
            )
        ]
        return action_list


class ApprovalHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Approval
    template_name = 'mooringlicensing/reversion_history.html'


class ComplianceHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Compliance
    template_name = 'mooringlicensing/reversion_history.html'



class HelpPageHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = HelpPage
    template_name = 'mooringlicensing/reversion_history.html'


class PreviewLicencePDFView(View):
    def post(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')

        proposal = self.get_object()
        details = json.loads(request.POST.get('formData'))

        response.write(proposal.preview_approval(request, details))
        return response

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs['proposal_pk'])


#from mooringlicensing.components.proposals.utils import test_proposal_emails
class TestEmailView(View):
    def get(self, request, *args, **kwargs):
        #test_proposal_emails(request)
        return HttpResponse('Test Email Script Completed')


class AuthorisedUserApplicationEndorseView(TemplateView):

    def get_object(self):
        return get_object_or_404(AuthorisedUserApplication, uuid=self.kwargs['uuid_str'])

    def get(self, request, *args, **kwargs):
        proposal = self.get_object()

        if not proposal.processing_status == Proposal.PROCESSING_STATUS_AWAITING_ENDORSEMENT:
            raise ValidationError('You cannot endorse/decline the application not in awaiting-endorsement status')

        action = self.kwargs['action']
        if action == 'endorse':
            self.template_name = 'mooringlicensing/proposals/authorised_user_application_endorsed.html'
            proposal.endorse_approved(request)
            # TODO: Upon endorsement, the applicant and site licensee receive an email
        elif action == 'decline':
            self.template_name = 'mooringlicensing/proposals/authorised_user_application_declined.html'
            proposal.endorse_declined(request)
            # TODO: Upon endorsement, the applicant and site licensee receive an email
        proposal.save()

        mooring = Mooring.private_moorings.get(id=proposal.mooring_site_id)

        context = {
            'proposal': proposal,
            'mooring': mooring,
        }

        return render(request, self.template_name, context)