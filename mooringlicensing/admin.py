from django.contrib.admin import AdminSite
from django.contrib import admin
from ledger_api_client.ledger_models import EmailUserRO

admin.site.index_template = 'admin-index.html'
admin.autodiscover()

class MooringLicensingAdminSite(AdminSite):
    site_header = 'Mooring Licensing Administration'
    site_title = 'Mooring Licensing Licensing'
    index_title = 'Mooring Licensing Licensing'

mooringlicensing_admin_site = MooringLicensingAdminSite(name='mooringlicensingadmin')
 
@admin.register(EmailUserRO)
class EmailUserROAdmin(admin.ModelAdmin):
    list_display = ('email','first_name','last_name','is_staff','is_active',)
    ordering = ('email',)
    search_fields = ('id','email','first_name','last_name')
    readonly_fields = ['email','first_name','last_name','is_staff','is_active','user_permissions']
 
    def has_delete_permission(self, request, obj=None):
        return False
