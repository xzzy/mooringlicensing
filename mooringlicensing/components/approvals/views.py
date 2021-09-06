from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect, get_object_or_404

from mooringlicensing import settings


class DcvPermitFormView(TemplateView):
    template_name = 'mooringlicensing/approvals/dcv_permit_form.html'

    # def get_object(self):
    #     return get_object_or_404(MooringLicenceApplication, uuid=self.kwargs['uuid_str'])

    def get(self, request, *args, **kwargs):
        # proposal = self.get_object()

        debug = self.request.GET.get('debug', 'f')
        if debug.lower() in ['true', 't', 'yes', 'y']:
            debug = True
        else:
            debug = False

        # if not proposal.processing_status == Proposal.PROCESSING_STATUS_AWAITING_DOCUMENTS:
        #     if not debug:
        #         raise ValidationError('You cannot upload documents for the application when it is not in awaiting-documents status')

        context = {}
        # context = {
        #     'proposal': proposal,
        #     'dev': settings.DEV_STATIC,
        #     'dev_url': settings.DEV_STATIC_URL
        # }

        if hasattr(settings, 'DEV_APP_BUILD_URL') and settings.DEV_APP_BUILD_URL:
            context['app_build_url'] = settings.DEV_APP_BUILD_URL

        return render(request, self.template_name, context)


class DcvAdmissionFormView(TemplateView):
    template_name = 'mooringlicensing/approvals/dcv_admission_form.html'

    def get(self, request, *args, **kwargs):

        if self.request.user.is_authenticated():
            return redirect('/external/dcv_admission')

        context = {}

        if hasattr(settings, 'DEV_APP_BUILD_URL') and settings.DEV_APP_BUILD_URL:
            context['app_build_url'] = settings.DEV_APP_BUILD_URL

        return render(request, self.template_name, context)


