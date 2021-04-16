from django.contrib import admin

from mooringlicensing.components.main.models import VesselSizeCategory, VesselSizeCategoryGroup, ApplicationType


class VesselSizeCategoryInline(admin.TabularInline):
    model = VesselSizeCategory
    extra = 0
    can_delete = True


@admin.register(VesselSizeCategoryGroup)
class VesselSizeCategoryGroupAdmin(admin.ModelAdmin):
    inlines = [VesselSizeCategoryInline,]


@admin.register(ApplicationType)
class ApplicationTypeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'code', 'description', 'oracle_code',]
    readonly_fields = ['code', 'description',]

    def get_actions(self, request):
        actions = super(ApplicationTypeAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
