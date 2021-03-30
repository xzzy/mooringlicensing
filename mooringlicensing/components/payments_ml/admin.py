from django.contrib import admin
from mooringlicensing.components.payments_ml.models import FeeSeason, FeePeriod


class FeePeriodInline(admin.TabularInline):
    model = FeePeriod
    extra = 0
    can_delete = True


@admin.register(FeeSeason)
class FeeSeasonAdmin(admin.ModelAdmin):
    inlines = [FeePeriodInline,]
