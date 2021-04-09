from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib import admin
from django.db.models import Min

from mooringlicensing.components.payments_ml.models import FeeSeason, FeePeriod, FeeConstructor, FeeItem, ApplicationFee
from mooringlicensing.components.proposals.models import ProposalType


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


class FeePeriodInline(admin.TabularInline):
    model = FeePeriod
    extra = 0
    can_delete = True
    formset = FeePeriodFormSet


class FeeSeasonForm(forms.ModelForm):
    class Meta:
        model = FeeSeason
        fields = '__all__'

    def clean(self):
        cleaned_data = super(FeeSeasonForm, self).clean()
        if cleaned_data['name']:
            return cleaned_data
        else:
            raise forms.ValidationError('Please enter the name field.')


class FeeItemInline(admin.TabularInline):
    model = FeeItem
    extra = 0
    can_delete = False
    readonly_fields = ('fee_period', 'vessel_size_category', 'proposal_type')
    max_num = 0  # This removes 'Add another ...' button

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(FeeItemInline, self).get_formset(request, obj, **kwargs)
        # form = formset.form
        # widget = form.base_fields['fee_period'].widget
        # widget.can_change_related = False
        return formset


class FeeConstructorForm(forms.ModelForm):
    class Meta:
        model = FeeConstructor
        fields = '__all__'

    def clean_application_type(self):
        data = self.cleaned_data['application_type']
        if self.instance.num_of_times_used_for_payment:
            # This fee_constructor object has been used at least once.
            if data != self.instance.application_type:
                raise forms.ValidationError('Application type cannot be changed once used for payment calculation')
        return data

    def clean_vessel_size_category_group(self):
        data = self.cleaned_data['vessel_size_category_group']
        if self.instance.num_of_times_used_for_payment:
            # This fee_constructor object has been used at least once.
            if data != self.instance.vessel_size_category_group:
                raise forms.ValidationError('Vessel size category group cannot be changed once used for payment calculation')
        return data

    def clean_fee_season(self):
        data = self.cleaned_data['fee_season']
        if self.instance.num_of_times_used_for_payment:
            # This fee_constructor object has been used at least once.
            if data != self.instance.fee_season:
                raise forms.ValidationError('Fee season cannot be changed once used for payment calculation')
        return data

    def clean_incur_gst(self):
        data = self.cleaned_data['incur_gst']
        if self.instance.num_of_times_used_for_payment:
            # This fee_constructor object has been used at least once.
            if data != self.instance.incur_gst:
                # Once used, application_type must not be changed
                raise forms.ValidationError('Incur gst cannot be changed once used for payment calculation')
        return data

    def clean(self):
        cleaned_data = super(FeeConstructorForm, self).clean()
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
        if db_field.name == "fee_season":
            kwargs["queryset"] = FeeSeason.objects.annotate(s_date=Min("fee_periods__start_date")).order_by('s_date')
        return super(FeeConstructorAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
