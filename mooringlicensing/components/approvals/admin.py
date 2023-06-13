from django.contrib import admin

from mooringlicensing.components.approvals import models


@admin.register(models.Sticker)
class StickerAdmin(admin.ModelAdmin):
    list_display = ['number', 'status', 'approval', 'dcv_permit', 'printing_date', 'mailing_date', 'fee_season',]