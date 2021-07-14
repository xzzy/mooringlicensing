from django import forms
from django.contrib import admin

from mooringlicensing.components.main.models import VesselSizeCategory, VesselSizeCategoryGroup, ApplicationType, \
    NumberOfDaysSetting, NumberOfDaysType


class VesselSizeCategoryForm(forms.ModelForm):

    model = VesselSizeCategory
    fields = '__all__'

    def clean_name(self):
        data = self.cleaned_data.get('name')
        if not self.instance.is_editable:
            if data != self.instance.name:
                raise forms.ValidationError('Name cannot be changed once used for payment calculation.')
        return data

    def clean_start_size(self):
        data = self.cleaned_data.get('start_size')
        if not self.instance.is_editable:
            if data != self.instance.start_size:
                raise forms.ValidationError('Start size cannot be changed once used for payment calculation.')
        return data

    def clean_include_start_size(self):
        data = self.cleaned_data.get('include_start_size')
        if not self.instance.is_editable:
            if data != self.instance.include_start_size:
                raise forms.ValidationError('Include start size cannot be changed once used for payment calculation.')
        return data

    def clean(self):
        cleaned_data = super(VesselSizeCategoryForm, self).clean()

        return cleaned_data


class VesselSizeCategoryFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        '''
        Validate forms as a whole
        '''
        null_vessel_count = 0
        size_list = []

        for form in self.forms:
            if form.cleaned_data['null_vessel']:
                null_vessel_count += 1
            if form.cleaned_data['start_size'] in size_list:
                raise forms.ValidationError('There is a duplicate vessel size: {}'.format(form.cleaned_data['start_size']))
            else:
                size_list.append(form.cleaned_data['start_size'])

        if null_vessel_count >= 2:
            raise forms.ValidationError('There should not be more than 1 null-vessel catergories.  There are {}'.format(null_vessel_count))


class VesselSizeCategoryInline(admin.TabularInline):
    model = VesselSizeCategory
    extra = 0
    can_delete = True
    form = VesselSizeCategoryForm
    formset = VesselSizeCategoryFormset


class VesselSizeCategoryGroupForm(forms.ModelForm):

    model = VesselSizeCategoryGroup
    fields = '__all__'

    def clean_name(self):
        data = self.cleaned_data.get('name')

        if not self.instance.is_editable:
            if data != self.instance.name:
                raise forms.ValidationError('Name cannot be changed once used for payment calculation.')
        if not data:
            raise forms.ValidationError('Please enter the name field.')

        return data

    def clean(self):
        cleaned_data = super(VesselSizeCategoryGroupForm, self).clean()

        return cleaned_data


@admin.register(VesselSizeCategoryGroup)
class VesselSizeCategoryGroupAdmin(admin.ModelAdmin):
    inlines = [VesselSizeCategoryInline,]
    form = VesselSizeCategoryGroupForm


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


class NumberOfDaysSettingInline(admin.TabularInline):
    model = NumberOfDaysSetting
    extra = 0
    can_delete = True
    # form = VesselSizeCategoryForm


@admin.register(NumberOfDaysType)
class NumberOfDaysTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'number_by_date',]
    list_display_links = ['name',]
    # readonly_fields = ['name',]
    fields = ['name', 'description',]
    inlines = [NumberOfDaysSettingInline,]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# @admin.register(NumberOfDaysSetting)
# class NumberOfDaysSettingAdmin(admin.ModelAdmin):
#     list_display = [
#         'number_of_days',
#         'date_of_enforcement',
#         'number_of_days_type',
#     ]
