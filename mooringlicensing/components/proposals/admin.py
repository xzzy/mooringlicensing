from django.contrib import admin
from django.contrib.admin.utils import flatten_fieldsets

from ledger.accounts.models import EmailUser

from mooringlicensing.components.proposals import models
from mooringlicensing.components.proposals import forms
from mooringlicensing.components.main.models import (
    SystemMaintenance,
    Question,
    GlobalSettings,
)
from reversion.admin import VersionAdmin
from django.conf.urls import url
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseRedirect
from mooringlicensing.components.proposals.models import StickerPrintingBatch, StickerPrintingResponse, \
    StickerPrintingContact


class ProposalDocumentInline(admin.TabularInline):
    model = models.ProposalDocument
    extra = 0

@admin.register(models.AmendmentReason)
class AmendmentReasonAdmin(admin.ModelAdmin):
    list_display = ['reason']


@admin.register(models.Proposal)
class ProposalAdmin(VersionAdmin):
    list_display = ['id', 'lodgement_number', 'lodgement_date', 'processing_status', 'submitter', 'approval',]
    list_display_links = ['id', 'lodgement_number', ]
    inlines =[ProposalDocumentInline,]


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


@admin.register(SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'start_date', 'end_date', 'duration']
    ordering = ('start_date',)
    readonly_fields = ('duration',)
    form = forms.SystemMaintenanceAdminForm


@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', '_file',]
    ordering = ('key',)

    def get_fields(self, request, obj=None):
        if obj and obj.key in GlobalSettings.keys_for_file:
            return ['key', '_file',]
        else:
            return ['key', 'value', 'stickerprintingcontact_set',]

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ['key',]

    def has_delete_permission(self, request, obj=None):
        if obj:
            if obj.key in [item[0] for item in GlobalSettings.keys]:
                return False
        return True


@admin.register(StickerPrintingContact)
class StickersPrintingContactAdmin(admin.ModelAdmin):
    list_display = ['email', 'type', 'enabled',]
    ordering = ('type', 'email',)


@admin.register(StickerPrintingBatch)
class StickersPrintingBatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', '_file', 'uploaded_date', 'emailed_datetime',]
    list_display_links = ['id', 'name', '_file',]

    def get_actions(self, request):
        actions = super(StickersPrintingBatchAdmin, self).get_actions(request)
        del actions["delete_selected"]
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    def get_readonly_fields(self, request, obj=None):
        return [
            'id',
            'name',
            'emailed_datetime',
            'uploaded_date',
            '_file',
        ]

    def save_model(self, request, obj, form, change):
        pass

    def delete_model(self, request, obj):
        pass

    def save_related(self, request, form, formsets, change):
        pass


@admin.register(StickerPrintingResponse)
class StickersPrintingResponseAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', '_file', 'uploaded_date', 'received_datetime',]

    def get_actions(self, request):
        actions = super(StickersPrintingResponseAdmin, self).get_actions(request)
        del actions["delete_selected"]
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    def get_readonly_fields(self, request, obj=None):
        return [
            'id',
            'name',
            'received_datetime',
            'uploaded_date',
            '_file',
        ]

    def save_model(self, request, obj, form, change):
        pass

    def delete_model(self, request, obj):
        pass

    def save_related(self, request, form, formsets, change):
        pass
