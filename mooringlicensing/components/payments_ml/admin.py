from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib import admin
from mooringlicensing.components.payments_ml.models import FeeSeason, FeePeriod, FeeConstructor


class FeePeriodFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        num_of_periods = len(self.cleaned_data)
        if num_of_periods == 1:
            # There is one period configured
            # All fine
            pass
        elif num_of_periods > 1:
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

        else:
            # No periods configured for this season
            raise forms.ValidationError('At lease one period must exist in a season.')


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


###### Admins from here #####
@admin.register(FeeSeason)
class FeeSeasonAdmin(admin.ModelAdmin):
    form = FeeSeasonForm
    inlines = [FeePeriodInline,]


@admin.register(FeeConstructor)
class FeeConstructorAdmin(admin.ModelAdmin):
    pass