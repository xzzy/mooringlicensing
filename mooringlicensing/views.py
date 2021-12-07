import logging
from confy import env
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from mooringlicensing.helpers import is_internal
from mooringlicensing.forms import *
from mooringlicensing.components.proposals.models import (
        Proposal, 
        HelpPage
        )
from mooringlicensing.components.compliances.models import Compliance
from django.core.management import call_command


logger = logging.getLogger('mooringlicensing')


class InternalView(UserPassesTestMixin, TemplateView):
    template_name = 'mooringlicensing/dash/index.html'

    def test_func(self):
        return is_internal(self.request)

    def get_context_data(self, **kwargs):
        context = super(InternalView, self).get_context_data(**kwargs)
        context['dev'] = settings.DEV_STATIC
        context['dev_url'] = settings.DEV_STATIC_URL
        if hasattr(settings, 'DEV_APP_BUILD_URL') and settings.DEV_APP_BUILD_URL:
            context['app_build_url'] = settings.DEV_APP_BUILD_URL
        return context


class ExternalView(LoginRequiredMixin, TemplateView):
    template_name = 'mooringlicensing/dash/index.html'

    def get_context_data(self, **kwargs):
        context = super(ExternalView, self).get_context_data(**kwargs)
        context['dev'] = settings.DEV_STATIC
        context['dev_url'] = settings.DEV_STATIC_URL
        if hasattr(settings, 'DEV_APP_BUILD_URL') and settings.DEV_APP_BUILD_URL:
            context['app_build_url'] = settings.DEV_APP_BUILD_URL
        return context


class ExternalProposalView(DetailView):
    model = Proposal
    template_name = 'mooringlicensing/dash/index.html'

class ExternalComplianceView(DetailView):
    model = Compliance
    template_name = 'mooringlicensing/dash/index.html'

class InternalComplianceView(DetailView):
    model = Compliance
    template_name = 'mooringlicensing/dash/index.html'


class MooringLicensingRoutingView(TemplateView):
    template_name = 'mooringlicensing/index.html'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            if is_internal(self.request):
                return redirect('internal')
            return redirect('external')
        kwargs['form'] = LoginForm
        return super(MooringLicensingRoutingView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MooringLicensingRoutingView, self).get_context_data(**kwargs)
        daily_admission_page_url = env('DAILY_ADMISSION_PAGE_URL', '')
        context.update({
            'daily_admission_page_url': daily_admission_page_url
        })
        return context


class MooringLicensingContactView(TemplateView):
    template_name = 'mooringlicensing/contact.html'


class MooringLicensingFurtherInformationView(TemplateView):
    template_name = 'mooringlicensing/further_info.html'


class InternalProposalView(DetailView):
    model = Proposal
    template_name = 'mooringlicensing/dash/index.html'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            if is_internal(self.request):
                return super(InternalProposalView, self).get(*args, **kwargs)
            return redirect('external-proposal-detail')
        kwargs['form'] = LoginForm
        return super(MooringLicensingRoutingDetailView, self).get(*args, **kwargs)


@login_required(login_url='ds_home')
def first_time(request):
    context = {}
    if request.method == 'POST':
        form = FirstTimeForm(request.POST)
        redirect_url = form.data['redirect_url']
        if not redirect_url:
            redirect_url = '/'
        if form.is_valid():
            # set user attributes
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.dob = form.cleaned_data['dob']
            request.user.save()
            return redirect(redirect_url)
        context['form'] = form
        context['redirect_url'] = redirect_url
        return render(request, 'mooringlicensing/user_profile.html', context)
    # GET default
    if 'next' in request.GET:
        context['redirect_url'] = request.GET['next']
    else:
        context['redirect_url'] = '/'
    context['dev'] = settings.DEV_STATIC
    context['dev_url'] = settings.DEV_STATIC_URL
    return render(request, 'mooringlicensing/dash/index.html', context)


class HelpView(LoginRequiredMixin, TemplateView):
    template_name = 'mooringlicensing/help.html'

    def get_context_data(self, **kwargs):
        context = super(HelpView, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated():
            application_type = kwargs.get('application_type', None)
            if kwargs.get('help_type', None)=='assessor':
                if is_internal(self.request):
                    qs = HelpPage.objects.filter(application_type__name__icontains=application_type, help_type=HelpPage.HELP_TEXT_INTERNAL).order_by('-version')
                    context['help'] = qs.first()
            else:
                qs = HelpPage.objects.filter(application_type__name__icontains=application_type, help_type=HelpPage.HELP_TEXT_EXTERNAL).order_by('-version')
                context['help'] = qs.first()
        return context


class ManagementCommandsView(LoginRequiredMixin, TemplateView):
    template_name = 'mooringlicensing/mgt-commands.html'

    def get(self, request, *args, **kwargs):
        debug = request.GET.get('debug', 'f')
        if debug.lower() in ['true', 't', 'yes', 'y']:
            debug = True
        else:
            debug = False

        context = self.get_context_data(**kwargs)
        context.update({'debug': debug})
        return self.render_to_response(context)

    def post(self, request):
        data = {}
        command_script = request.POST.get('script', None)

        if command_script:
            print('running {}'.format(command_script))
            call_command(command_script, params=request.POST)
            data.update({command_script: 'true'})

        return render(request, self.template_name, data)

