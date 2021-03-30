from django.contrib import admin

from mooringlicensing.components.main.models import VesselSizeCategory, VesselSizeCategoryGroup


class VesselSizeCategoryInline(admin.TabularInline):
    model = VesselSizeCategory
    extra = 0
    can_delete = True


@admin.register(VesselSizeCategoryGroup)
class FeeSeasonAdmin(admin.ModelAdmin):
    inlines = [VesselSizeCategoryInline,]
