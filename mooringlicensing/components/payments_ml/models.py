import datetime
from decimal import Decimal

import pytz
from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import Q
from ledger.accounts.models import RevisionedMixin, EmailUser
from ledger.payments.invoice.models import Invoice
from ledger.settings_base import TIME_ZONE

from mooringlicensing.components.main.models import ApplicationType, VesselSizeCategoryGroup, VesselSizeCategory
from mooringlicensing.components.proposals.models import Proposal, ProposalType


class Payment(RevisionedMixin):
    send_invoice = models.BooleanField(default=False)
    confirmation_sent = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        app_label = 'mooringlicensing'
        abstract = True

    @property
    def paid(self):
        payment_status = self.__check_payment_status()
        if payment_status == 'paid' or payment_status == 'over_paid':
            return True
        return False

    @property
    def unpaid(self):
        payment_status = self.__check_payment_status()
        if payment_status == 'unpaid':
            return True
        return False

    @property
    def amount_paid(self):
        return self.__check_payment_amount()

    def __check_payment_amount(self):
        amount = Decimal('0.0')
        if self.active_invoice:
            return self.active_invoice.payment_amount
        return amount

    def __check_invoice_payment_status(self):
        invoices = []
        payment_amount = Decimal('0.0')
        invoice_amount = Decimal('0.0')
        references = self.invoices.all().values('invoice_reference')
        for r in references:
            try:
                invoices.append(Invoice.objects.get(reference=r.get("invoice_reference")))
            except Invoice.DoesNotExist:
                pass
        for i in invoices:
            if not i.voided:
                payment_amount += i.payment_amount
                invoice_amount += i.amount

        if invoice_amount == payment_amount:
            return 'paid'
        if payment_amount > invoice_amount:
            return 'over_paid'
        return "unpaid"

    def __check_payment_status(self):
        invoices = []
        amount = Decimal('0.0')
        references = self.invoices.all().values('invoice_reference')
        for r in references:
            try:
                invoices.append(Invoice.objects.get(reference=r.get("invoice_reference")))
            except Invoice.DoesNotExist:
                pass
        for i in invoices:
            if not i.voided:
                amount += i.payment_amount

        if amount == 0:
            return 'unpaid'
        elif self.cost_total < amount:
            return 'over_paid'
        elif self.cost_total > amount:
            return 'partially_paid'
        return "paid"


class ApplicationFee(Payment):
    PAYMENT_TYPE_INTERNET = 0
    PAYMENT_TYPE_RECEPTION = 1
    PAYMENT_TYPE_BLACK = 2
    PAYMENT_TYPE_TEMPORARY = 3
    PAYMENT_TYPE_CHOICES = (
        (PAYMENT_TYPE_INTERNET, 'Internet booking'),
        (PAYMENT_TYPE_RECEPTION, 'Reception booking'),
        (PAYMENT_TYPE_BLACK, 'Black booking'),
        (PAYMENT_TYPE_TEMPORARY, 'Temporary reservation'),
    )

    proposal = models.ForeignKey(Proposal, on_delete=models.PROTECT, blank=True, null=True, related_name='application_fees')
    payment_type = models.SmallIntegerField(choices=PAYMENT_TYPE_CHOICES, default=0)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    created_by = models.ForeignKey(EmailUser,on_delete=models.PROTECT, blank=True, null=True,related_name='created_by_application_fee')
    invoice_reference = models.CharField(max_length=50, null=True, blank=True, default='')

    def __str__(self):
        return 'Application {} : Invoice {}'.format(self.proposal, self.invoice_reference)

    class Meta:
        app_label = 'mooringlicensing'


class FeeSeason(RevisionedMixin):
    name = models.CharField(max_length=50, null=False, blank=False)
    # start_date = models.DateField(null=True, blank=True)
    # end_date = start_date + 1year

    def __str__(self):
        if self.start_date:
            return '{} ({} to {})'.format(self.name, self.start_date, self.end_date)
        else:
            return '{} (No periods found)'.format(self.name)

    def get_first_period(self):
        first_period = self.fee_periods.order_by('start_date').first()
        return first_period

    @property
    def is_editable(self):
        today_local = datetime.datetime.now(pytz.timezone(TIME_ZONE)).date()
        return True if today_local < self.start_date else False

    @property
    def start_date(self):
        first_period = self.get_first_period()
        return first_period.start_date if first_period else None

    @property
    def end_date(self):
        end_date = self.start_date + relativedelta(years=1) - relativedelta(days=1)
        return end_date

    class Meta:
        app_label = 'mooringlicensing'
        verbose_name = 'season'


class FeePeriod(RevisionedMixin):
    fee_season = models.ForeignKey(FeeSeason, null=True, blank=True, related_name='fee_periods')
    name = models.CharField(max_length=50, null=True, blank=True, default='')
    start_date = models.DateField(null=True, blank=True)
    # end_date = (next fee_period - 1day) or fee_season.end_date, which is start_date + 1year

    def __str__(self):
        return 'Name: {}, Start Date: {}'.format(self.name, self.start_date)

    class Meta:
        app_label = 'mooringlicensing'
        ordering = ['start_date']


class FeeConstructor(RevisionedMixin):
    application_type = models.ForeignKey(ApplicationType, null=True, blank=True)
    fee_season = models.ForeignKey(FeeSeason, null=True, blank=True)
    vessel_size_category_group = models.ForeignKey(VesselSizeCategoryGroup, null=True, blank=True)

    def __str__(self):
        return 'ApplicationType: {}, Season: {}, VesselSizeCategoryGroup: {}'.format(self.application_type.description, self.fee_season, self.vessel_size_category_group)

    def get_fee_item(self, proposal_type, vessel_length, target_date=datetime.datetime.now(pytz.timezone(TIME_ZONE)).date()):
        fee_period = self.fee_season.fee_periods.filter(start_date__lte=target_date).order_by('start_date').last()
        vessel_size_category = self.vessel_size_category_group.vessel_size_categories.filter(start_size__lte=vessel_length).order_by('start_size').last()
        fee_item = FeeItem.objects.filter(fee_constructor=self, fee_period=fee_period, vessel_size_category=vessel_size_category, proposal_type=proposal_type)

        if fee_item:
            return fee_item[0]
        else:
            # Fees are probably not configured yet...
            return None

    @classmethod
    def get_fee_constructor_by_application_type_and_date(cls, application_type, target_date=datetime.datetime.now(pytz.timezone(TIME_ZONE)).date()):
        fee_constructor_qs = cls.objects.filter(application_type=application_type,)
        target_fee_constructor = None
        for fee_constructor in fee_constructor_qs:
            if fee_constructor.fee_season.start_date <= target_date <= fee_constructor.fee_season.end_date:
                # Seasons which have already started, but not ended yet.
                if not target_fee_constructor or target_fee_constructor.fee_season.start_date < fee_constructor.fee_season.start_date:
                    # Pick the season which started most recently.
                    target_fee_constructor = fee_constructor
        return target_fee_constructor

    class Meta:
        app_label = 'mooringlicensing'
        # An application type cannot have the same fee_season multiple times.
        # Which means a vessel_size_category_group can be determined by the application_type and the fee_season
        unique_together = ('application_type', 'fee_season',)


class FeeItem(RevisionedMixin):
    fee_constructor = models.ForeignKey(FeeConstructor, null=True, blank=True)
    fee_period = models.ForeignKey(FeePeriod, null=True, blank=True)
    vessel_size_category = models.ForeignKey(VesselSizeCategory, null=True, blank=True)
    proposal_type = models.ForeignKey(ProposalType, null=True, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')

    def __str__(self):
        return '${}: ApplicationType: {}, Period: {}, VesselSizeCategory: {}'.format(self.amount, self.fee_constructor.application_type, self.fee_period, self.vessel_size_category)

    class Meta:
        app_label = 'mooringlicensing'
