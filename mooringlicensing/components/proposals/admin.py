from django.contrib import admin
from ledger.accounts.models import EmailUser
from mooringlicensing.components.proposals import models
#from mooringlicensing.components.bookings.models import ApplicationFeeInvoice
from mooringlicensing.components.proposals import forms
from mooringlicensing.components.main.models import (
    SystemMaintenance,
    #ApplicationType,
    #OracleCode,
    #RequiredDocument,
    Question,
    GlobalSettings,
)
#from mooringlicensing.components.main.models import Activity, SubActivityLevel1, SubActivityLevel2, SubCategory
from reversion.admin import VersionAdmin
from django.conf.urls import url
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseRedirect
#from mooringlicensing.utils import create_helppage_object
# Register your models here.

# Commented since COLS does not use schema - so will not require direct editing by user in Admin (although a ProposalType is still required for ApplicationType)
#@admin.register(models.ProposalType)
#class ProposalTypeAdmin(admin.ModelAdmin):
#    list_display = ['name','description', 'version']
#    ordering = ('name', '-version')
#    list_filter = ('name',)
    #exclude=("site",)

class ProposalDocumentInline(admin.TabularInline):
    model = models.ProposalDocument
    extra = 0

@admin.register(models.AmendmentReason)
class AmendmentReasonAdmin(admin.ModelAdmin):
    list_display = ['reason']

@admin.register(models.Proposal)
class ProposalAdmin(VersionAdmin):
    inlines =[ProposalDocumentInline,]


@admin.register(models.ProposalAssessorGroup)
class ProposalAssessorGroupAdmin(admin.ModelAdmin):
    #list_display = ['name','default']
    filter_horizontal = ('members',)
    form = forms.ProposalAssessorGroupAdminForm
    #readonly_fields = ['default']
    #readonly_fields = ['regions', 'activities']

    def get_actions(self, request):
        actions = super(ProposalAssessorGroupAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        if self.model.objects.count() == 1:
            return False
        return super(ProposalAssessorGroupAdmin, self).has_delete_permission(request, obj)

    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        return super(ProposalAssessorGroupAdmin, self).has_add_permission(request)


@admin.register(models.ProposalApproverGroup)
class ProposalApproverGroupAdmin(admin.ModelAdmin):
    #list_display = ['name','default']
    filter_horizontal = ('members',)
    form = forms.ProposalApproverGroupAdminForm
    #readonly_fields = ['default']
    #readonly_fields = ['default', 'regions', 'activities']

    def get_actions(self, request):
        actions =  super(ProposalApproverGroupAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        if self.model.objects.count() == 1:
            return False
        return super(ProposalApproverGroupAdmin, self).has_delete_permission(request, obj)

    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        return super(ProposalApproverGroupAdmin, self).has_add_permission(request)

@admin.register(models.ProposalStandardRequirement)
class ProposalStandardRequirementAdmin(admin.ModelAdmin):
    list_display = [
            'code',
            'text',
            'obsolete', 
            #'application_type', 
            'participant_number_required', 
            'default'
            ]

#@admin.register(models.HelpPage)
#class HelpPageAdmin(admin.ModelAdmin):
#    list_display = ['application_type','help_type', 'description', 'version']
#    form = forms.MooringLicensingHelpPageAdminForm
#    change_list_template = "mooringlicensing/help_page_changelist.html"
#    ordering = ('application_type', 'help_type', '-version')
#    list_filter = ('application_type', 'help_type')
#
#
#    def get_urls(self):
#        urls = super(HelpPageAdmin, self).get_urls()
#        my_urls = [
#            url('create_mooringlicensing_help/', self.admin_site.admin_view(self.create_mooringlicensing_help)),
#            url('create_mooringlicensing_help_assessor/', self.admin_site.admin_view(self.create_mooringlicensing_help_assessor)),
#        ]
#        return my_urls + urls
#
#    def create_mooringlicensing_help(self, request):
#        create_helppage_object(application_type='T Class', help_type=models.HelpPage.HELP_TEXT_EXTERNAL)
#        return HttpResponseRedirect("../")
#
#    def create_mooringlicensing_help_assessor(self, request):
#        create_helppage_object(application_type='T Class', help_type=models.HelpPage.HELP_TEXT_INTERNAL)
#        return HttpResponseRedirect("../")

@admin.register(models.ChecklistQuestion)
class ChecklistQuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 
            #'application_type',
            'list_type', 
            'obsolete',
            'answer_type', 
            'order'
            ]
    ordering = ('order',)

@admin.register(SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'start_date', 'end_date', 'duration']
    ordering = ('start_date',)
    readonly_fields = ('duration',)
    form = forms.SystemMaintenanceAdminForm

#@admin.register(ApplicationType)
#class ApplicationTypeAdmin(admin.ModelAdmin):
#    ordering = ('order',)

#@admin.register(ApplicationType)
#class ApplicationTypeAdmin(admin.ModelAdmin):
#    list_display = ['name', 'order', 'visible', 'max_renewals', 'max_renewal_period', 'application_fee']
#    ordering = ('order',)
#
#    def get_form(self, request, obj=None, **kwargs):
#        self.exclude = ()
#        if obj.name == ApplicationType.EVENT:
#            self.exclude = (
#                "max_renewals", "max_renewal_period", "licence_fee_2mth", "licence_fee_1yr",
#                "filming_fee_half_day", "filming_fee_full_day", "filming_fee_2days", "filming_fee_3days",
#                "photography_fee_half_day", "photography_fee_full_day", "photography_fee_2days", "photography_fee_3days",
#            )
#        elif obj.name == ApplicationType.FILMING:
#            self.exclude = (
#                "max_renewals", "max_renewal_period", "licence_fee_2mth", "licence_fee_1yr",
#                "events_park_fee",
#            )
#        elif obj.name == ApplicationType.TCLASS:
#            self.exclude = (
#                "filming_fee_half_day", "filming_fee_full_day", "filming_fee_2days", "filming_fee_3days",
#                "photography_fee_half_day", "photography_fee_full_day", "photography_fee_2days", "photography_fee_3days",
#                "events_park_fee",
#            )
#        elif obj.name == ApplicationType.ECLASS:
#            self.exclude = (
#                "max_renewals", "max_renewal_period", "licence_fee_2mth", "licence_fee_1yr",
#                "filming_fee_half_day", "filming_fee_full_day", "filming_fee_2days", "filming_fee_3days",
#                "photography_fee_half_day", "photography_fee_full_day", "photography_fee_2days", "photography_fee_3days",
#                "events_park_fee",
#            )
#
#        form = super(ApplicationTypeAdmin, self).get_form(request, obj, **kwargs)
#        return form


#class OracleCodeInline(admin.TabularInline):
#    model = OracleCode
#    exclude = ['archive_date']
#    extra = 3
#    max_num = 3
#    can_delete = False

#@admin.register(models.Vessel)
#class VesselAdmin(admin.ModelAdmin):
#    list_display = ['nominated_vessel','spv_no', 'hire_rego', 'craft_no', 'size', 'proposal']
#    ordering = ('nominated_vessel',)


@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        if obj.key == GlobalSettings.KEY_DCV_PERMIT_TEMPLATE_FILE:
            return ['key', '_file',]
        else:
            return ['key', 'value',]

    def get_readonly_fields(self, request, obj=None):
        return ['key',]

    list_display = ['key', 'value', '_file',]
    ordering = ('key',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'answer_one', 'answer_two', 'answer_three', 'answer_four', 
            #application_type',
            ]
    ordering = ('question_text',)

