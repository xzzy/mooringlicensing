from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect, get_object_or_404

from mooringlicensing import settings


class DcvPermitFormView(TemplateView):
    template_name = 'mooringlicensing/approvals/dcv_permit_form.html'

    def get(self, request, *args, **kwargs):

        debug = self.request.GET.get('debug', 'f')
        if debug.lower() in ['true', 't', 'yes', 'y']:
            debug = True
        else:
            debug = False

        context = {}

        if hasattr(settings, 'DEV_APP_BUILD_URL') and settings.DEV_APP_BUILD_URL:
            context['app_build_url'] = settings.DEV_APP_BUILD_URL

        return render(request, self.template_name, context)


class DcvAdmissionFormView(TemplateView):
    template_name = 'mooringlicensing/approvals/dcv_admission_form.html'

    def get(self, request, *args, **kwargs):

        if self.request.user.is_authenticated:
            return redirect('/external/dcv_admission')

        context = {}

        if hasattr(settings, 'DEV_APP_BUILD_URL') and settings.DEV_APP_BUILD_URL:
            context['app_build_url'] = settings.DEV_APP_BUILD_URL

        return render(request, self.template_name, context)


