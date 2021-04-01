from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib import admin
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


class FeeConstructorForm(forms.ModelForm):
    class Meta:
        model = FeeConstructor
        fields = '__all__'

    def clean(self):
        pass


###### Admins from here #####
@admin.register(FeeSeason)
class FeeSeasonAdmin(admin.ModelAdmin):
    form = FeeSeasonForm
    inlines = [FeePeriodInline,]


@admin.register(FeeConstructor)
class FeeConstructorAdmin(admin.ModelAdmin):
    form = FeeConstructorForm
    inlines = [FeeItemInline,]