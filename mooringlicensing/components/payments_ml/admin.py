from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib import admin
from mooringlicensing.components.payments_ml.models import FeeSeason, FeePeriod, FeeConstructor, FeeItem
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
            # Check if all the period sit in one year span
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
        if self.cleaned_data['name']:
            return self.cleaned_data
        else:
            raise forms.ValidationError('Please enter the name field.')


class FeeItemInline(admin.TabularInline):
    model = FeeItem
    extra = 0
    can_delete = False
    readonly_fields = ('fee_period', 'proposal_type', 'vessel_size_category')
    max_num = 0

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

    def clean(self):
        fee_constructor = self.instance
        proposal_types = ProposalType.objects.all()

        application_type = self.cleaned_data['application_type']
        print(application_type.description)
        for fee_period in self.cleaned_data['fee_season'].fee_periods.all():
            for vessel_size_category in self.cleaned_data['vessel_size_category_group'].vessel_size_categories.all():
                for proposal_type in proposal_types:
                    fee_item, created = FeeItem.objects.get_or_create(fee_constructor=fee_constructor, fee_period=fee_period, vessel_size_category=vessel_size_category, proposal_type=proposal_type)
                    if created:
                        print('Created: {} - {} - {}'.format(fee_period.name, vessel_size_category.name, proposal_type.description))


@admin.register(FeeSeason)
class FeeSeasonAdmin(admin.ModelAdmin):
    form = FeeSeasonForm
    inlines = [FeePeriodInline,]


@admin.register(FeeConstructor)
class FeeConstructorAdmin(admin.ModelAdmin):
    form = FeeConstructorForm
    inlines = [FeeItemInline,]