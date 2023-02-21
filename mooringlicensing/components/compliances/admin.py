from django.contrib import admin
from mooringlicensing.components.compliances import models
# Register your models here.


@admin.register(models.ComplianceAmendmentReason)
class ComplianceAmendmentReasonAdmin(admin.ModelAdmin):
    list_display = ['reason']

