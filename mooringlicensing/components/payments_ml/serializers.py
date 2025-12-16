from rest_framework import serializers

from mooringlicensing.components.approvals.models import (
    DcvPermit, DcvVessel, DcvAdmission, 
    DcvAdmissionArrival, NumberOfPeople, AgeGroup
)
from mooringlicensing.components.payments_ml.models import (
    FeeSeason, FeeConstructor, ApplicationFee, StickerActionFee
)

from django.conf import settings
from ledger_api_client.ledger_models import Invoice

class InvoiceListSerializer(serializers.ModelSerializer):

    fee_source = serializers.SerializerMethodField()
    fee_source_type = serializers.SerializerMethodField()
    fee_source_id = serializers.SerializerMethodField()
    ledger_link = serializers.SerializerMethodField()
    created_str = serializers.SerializerMethodField()
    settlement_date_str = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = (
            'id',
            'created',
            'text',
            'reference',
            'fee_source',
            'fee_source_type',
            'fee_source_id',
            'amount',
            'order_number',
            'voided',
            'settlement_date',
            'created_str',
            'settlement_date_str',
            'ledger_link',
        )

        datatables_always_serialize = (
            'id',
            'created',
            'text',
            'reference',
            'fee_source',
            'fee_source_type',
            'fee_source_id',
            'amount',
            'order_number',
            'voided',
            'settlement_date',
            'created_str',
            'settlement_date_str',
            'ledger_link',
        )

    #TODO consider putting the three below funcs into a single object (reduce queries)
    def get_fee_source_type(self, obj):
        if ApplicationFee.objects.filter(invoice_reference=obj.reference).exists():
            return 'Application'
        elif StickerActionFee.objects.filter(invoice_reference=obj.reference).exists():
            return 'Sticker Action'
        return ''

    def get_fee_source(self, obj):  
        application_fee_qs = ApplicationFee.objects.filter(invoice_reference=obj.reference)
        sticker_action_fee_qs = StickerActionFee.objects.filter(invoice_reference=obj.reference)
        if application_fee_qs.exists():
            fee = application_fee_qs.first() 
            return fee.proposal.lodgement_number if fee.proposal else ''
        elif sticker_action_fee_qs.exists():
            fee = sticker_action_fee_qs.filter(invoice_reference=obj.reference).first() 
            sticker_numbers = []
            for sticker_action in fee.sticker_action_details.all():
                if sticker_action.approval:
                    sticker_numbers.append(sticker_action.approval.lodgement_number)
            return ','.join(list(set(sticker_numbers)))
        return ''

    def get_fee_source_id(self, obj):
        application_fee_qs = ApplicationFee.objects.filter(invoice_reference=obj.reference)
        sticker_action_fee_qs = StickerActionFee.objects.filter(invoice_reference=obj.reference)
        if application_fee_qs.exists():
            fee = application_fee_qs.first() 
            return fee.proposal.id if fee.proposal else ''
        elif sticker_action_fee_qs.exists():
            fee = sticker_action_fee_qs.filter(invoice_reference=obj.reference).first() 
            if fee.sticker_action_details.first():
                if fee.sticker_action_details.first().approval:
                    return fee.sticker_action_details.first().approval.id
        return ''

    def get_ledger_link(self, obj):
        return '{}/ledger/payments/oracle/payments?{}'.format(settings.LEDGER_UI_URL, obj.reference)

    def get_created_str(self, obj):
        created = ''
        if obj.created:
            created = obj.created.strftime('%d/%m/%Y')
        return created

    def get_settlement_date_str(self, obj):
        settlement_date = ''
        if obj.settlement_date:
            settlement_date = obj.settlement_date.strftime('%d/%m/%Y')
        return settlement_date
    

class DcvAdmissionSerializer(serializers.ModelSerializer):
    dcv_vessel_id = serializers.IntegerField(required=True)

    class Meta:
        model = DcvAdmission
        fields = (
            'id',
            'lodgement_number',
            'submitter', 
            'applicant',
            'skipper',
            'contact_number',
            'dcv_vessel_id',
            'date_created',
            'status',
        )
        read_only_fields = (
            'id',
            'lodgement_number',
            'date_created',
        )

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not self.partial:
            if not data['skipper']:
                field_errors['skipper'] = ['Please enter the skipper name.',]
            if not data['contact_number']:
                field_errors['contact_number'] = ['Please enter the contact number.',]

            # Raise errors
            if field_errors:
                raise serializers.ValidationError(field_errors)
            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)

        return data


class DcvAdmissionArrivalSerializer(serializers.ModelSerializer):
    arrival_date = serializers.DateField(input_formats=(['%d/%m/%Y']))
    departure_date = serializers.DateField(input_formats=(['%d/%m/%Y']))

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not self.partial:
            if not data.get('arrival_date', None):
                field_errors['year'] = ['Please enter an arrival date.',]
            if not data.get('departure_date', None):
                field_errors['year'] = ['Please enter an departure date.',]

            # Raise errors
            if field_errors:
                raise serializers.ValidationError(field_errors)
            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)
            
        return data

    class Meta:
        model = DcvAdmissionArrival
        fields = (
            'id',
            'arrival_date',
            'departure_date',
            'dcv_admission',
            'private_visit',
        )
        read_only_fields = (
            'id',
        )


class NumberOfPeopleSerializer(serializers.ModelSerializer):

    def validate(self, data):
        return data

    class Meta:
        model = NumberOfPeople
        fields = (
            'id',
            'number',
            'dcv_admission_arrival',
            'age_group',
            'admission_type',
        )
        read_only_fields = (
            'id',
        )


class FeeSeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeSeason
        fields = (
            'id',
            'name'
        )


class DcvPermitSimpleSerializer(serializers.ModelSerializer):
    fee_season = FeeSeasonSerializer()
    dcv_organisation_name = serializers.SerializerMethodField()

    class Meta:
        model = DcvPermit
        fields = (
            'lodgement_number',
            'fee_season',
            'dcv_organisation_name',
        )

    def get_dcv_organisation_name(self, obj):
        try:
            if obj.dcv_organisation:
                return obj.dcv_organisation.name
            else:
                return obj.applicant_obj.get_full_name() + ' (P)'
        except:
            return ''


class DcvPermitSerializer(serializers.ModelSerializer):
    dcv_vessel_id = serializers.IntegerField(required=True)
    dcv_organisation_id = serializers.IntegerField(required=True)
    fee_season_id = serializers.IntegerField(required=True)

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not self.partial:
            if not data['fee_season_id']:
                field_errors['Season'] = ['Please select a season.',]

            #exclude cancelled permits from this list
            dcv_permit_qs = DcvPermit.objects.exclude(status=DcvPermit.DCV_PERMIT_STATUS_CANCELLED).filter(
                dcv_vessel_id=data.get('dcv_vessel_id', 0),
                fee_season_id=data.get('fee_season_id', 0),
            )
            if dcv_permit_qs:
                dcv_vessel = DcvVessel.objects.get(id=data.get('dcv_vessel_id'))
                fee_season = FeeSeason.objects.get(id=data.get('fee_season_id'))
                non_field_errors.append(f'DcvPermit for the vessel: {dcv_vessel} for the season: {fee_season.name} has been already issued.')

            # Raise errors
            if field_errors:
                raise serializers.ValidationError(field_errors)
            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)

        return data

    def get_permits(self, obj):
        permit_urls = []
        for doc in obj.dcv_permit_documents.all():
            permit_urls.append(doc._file.url)

    class Meta:
        model = DcvPermit
        fields = (
            'id',
            'lodgement_number',
            'submitter',
            'applicant',
            'lodgement_datetime',
            'dcv_vessel_id',
            'dcv_organisation_id',
            'fee_season_id',
            'start_date',
            'end_date',
            'postal_address_line1',
            'postal_address_line2',
            'postal_address_line3',
            'postal_address_suburb',
            'postal_address_postcode',
            'postal_address_state',
            'postal_address_country',
            'status',
        )
        read_only_fields = (
            'id',
            'lodgement_number',
            'start_date',
            'end_date',
        )


class FeeConstructorSerializer(serializers.ModelSerializer):
    start_date = serializers.ReadOnlyField()
    end_date = serializers.ReadOnlyField()
    fee_season = FeeSeasonSerializer()
    fee_items = serializers.SerializerMethodField()

    class Meta:
        model = FeeConstructor
        fields = (
            'id',
            'start_date',
            'end_date',
            'fee_season',
            'incur_gst',
            'fee_items',
        )

    def get_fee_items(self, fee_constructor):
        fee_configurations = {}

        for age_group in AgeGroup.NAME_CHOICES:
            fee_configurations[age_group[0]] = {}
        for fee_item in fee_constructor.feeitem_set.all():
            if fee_item.admission_type:
                fee_configurations[fee_item.age_group.code].update({fee_item.admission_type.code: fee_item.amount})

        return fee_configurations

