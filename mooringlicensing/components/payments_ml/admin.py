from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib import admin
from django.db.models import Min

from mooringlicensing import settings
from mooringlicensing.components.main.models import ApplicationType
from mooringlicensing.components.payments_ml.models import FeeSeason, FeePeriod, FeeConstructor, FeeItem


class FeePeriodFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        num_of_periods = len(self.cleaned_data)
        if num_of_periods < 1:
            # No periods configured for this season
            raise forms.ValidationError('At lease one period must exist in a season.')
        elif num_of_periods == 1:
            # There is one period configured
            # All fine
            pass
        else:
            # There are more than one periods configured
            # Check if all the periods sit in one year span
            sorted_cleaned_data = sorted(self.cleaned_data, key=lambda item: item['start_date'])
            start_date = sorted_cleaned_data[0]['start_date']
            end_date = sorted_cleaned_data[num_of_periods - 1]['start_date']
            start_date_plus_year = start_date + relativedelta(years=1)
            if end_date < start_date_plus_year:
                # All periods sit within an year span
                pass
            else:
                raise forms.ValidationError('All periods must sit within one year span.')

            # Check if all the period have unique start_date
            temp = []
            for item in self.cleaned_data:
                if not item['start_date'] in temp:
                    temp.append(item['start_date'])
                else:
                    raise forms.ValidationError('Period\'s start date must be unique, but {} is duplicated.'.format(item['start_date']))

    # def clean_name(self):
    #     data = self.cleaned_data['name']
    #     if not self.instance.is_editable:
    #         if data != self.instance.name:
    #             raise forms.ValidationError('Fee period cannot be changed once used for payment calculation')
    #     return data


class FeePeriodForm(forms.ModelForm):
    class Meta:
        model = FeePeriod
        fields = '__all__'

    def clean_name(self):
        data = self.cleaned_data['name']
        if not self.instance.is_editable:
            if data != self.instance.name:
                raise forms.ValidationError('Fee period cannot be changed once used for payment calculation')
        return data


class FeePeriodInline(admin.TabularInline):
    model = FeePeriod
    extra = 0
    can_delete = True
    formset = FeePeriodFormSet
    # form = FeePeriodForm


class FeeSeasonForm(forms.ModelForm):
    class Meta:
        model = FeeSeason
        fields = '__all__'

    def clean_name(self):
        data = self.cleaned_data['name']

        if not self.instance.is_editable:
            if data != self.instance.name:
                raise forms.ValidationError('Fee season cannot be changed once used for payment calculation')
        if not data:
            raise forms.ValidationError('Please enter the name field.')

        return data

    # def clean(self):
    #     cleaned_data = super(FeeSeasonForm, self).clean()
    #     if cleaned_data['name']:
    #         return cleaned_data
    #     else:
    #         raise forms.ValidationError('Please enter the name field.')


class FeeItemForm(forms.ModelForm):
    class Meta:
        model = FeeItem
        fields = '__all__'

    def clean_amount(self):
        data = self.cleaned_data['amount']
        if not self.instance.is_editable:
            if data != self.instance.amount:
                raise forms.ValidationError('Fee item cannot be changed once used for payment calculation')
        return data


class FeeItemInline(admin.TabularInline):
    model = FeeItem
    extra = 0
    can_delete = False
    readonly_fields = ('fee_period', 'vessel_size_category', 'proposal_type')
    max_num = 0  # This removes 'Add another ...' button
    form = FeeItemForm

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(FeeItemInline, self).get_formset(request, obj, **kwargs)
        # form = formset.form
        # widget = form.base_fields['fee_period'].widget
        # widget.can_change_related = False
        return formset

    # def has_change_permission(self, request, obj=None):
    #     return True


class FeeConstructorForm(forms.ModelForm):
    class Meta:
        model = FeeConstructor
        fields = '__all__'

    def clean_application_type(self):
        data = self.cleaned_data['application_type']
        if not self.instance.is_editable:
            # This fee_constructor object has been used at least once.
            if data != self.instance.application_type:
                raise forms.ValidationError('Application type cannot be changed once used for payment calculation')
        return data

    def clean_vessel_size_category_group(self):
        data = self.cleaned_data['vessel_size_category_group']
        if not self.instance.is_editable:
            # This fee_constructor object has been used at least once.
            if data != self.instance.vessel_size_category_group:
                raise forms.ValidationError('Vessel size category group cannot be changed once used for payment calculation')
        return data

    def clean_fee_season(self):
        data = self.cleaned_data['fee_season']
        if not self.instance.is_editable:
            # This fee_constructor object has been used at least once.
            if data != self.instance.fee_season:
                raise forms.ValidationError('Fee season cannot be changed once used for payment calculation')
        return data

    def clean_incur_gst(self):
        data = self.cleaned_data['incur_gst']
        if not self.instance.is_editable:
            # This fee_constructor object has been used at least once.
            if data != self.instance.incur_gst:
                # Once used, application_type must not be changed
                raise forms.ValidationError('Incur gst cannot be changed once used for payment calculation')
        return data

    def clean(self):
        cleaned_data = super(FeeConstructorForm, self).clean()

        cleaned_application_type = cleaned_data.get('application_type', None)
        cleaned_fee_season = cleaned_data.get('fee_season', None)
        if cleaned_application_type and cleaned_application_type.code == settings.APPLICATION_TYPE_DCV_PERMIT['code']:
            # If application type is DcvPermit
            if cleaned_fee_season and cleaned_fee_season.fee_periods.count() > 1:
                # There are more than 1 period in the season
                raise forms.ValidationError('A season for the {} cannot have more than 1 period.  Selected season {} has {} periods.'.format(
                    cleaned_application_type.description,
                    cleaned_fee_season.name,
                    cleaned_fee_season.fee_periods.count(),
                ))

        return cleaned_data


@admin.register(FeeSeason)
class FeeSeasonAdmin(admin.ModelAdmin):
    form = FeeSeasonForm
    inlines = [FeePeriodInline,]


@admin.register(FeeConstructor)
class FeeConstructorAdmin(admin.ModelAdmin):
    form = FeeConstructorForm
    inlines = [FeeItemInline,]
    # list_display = ('__str__', 'incur_gst', 'enabled',)
    list_display = ('id', 'application_type', 'fee_season', 'vessel_size_category_group', 'incur_gst', 'enabled',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Sort 'fee_season' dropdown by the start_date
        if db_field.name == "fee_season":
            kwargs["queryset"] = FeeSeason.objects.annotate(s_date=Min("fee_periods__start_date")).order_by('s_date')
        return super(FeeConstructorAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
